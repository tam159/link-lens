"""Requests that spend on model calls: onboarding a snapshot, and catalogue discovery.

Dagster starts these and does not wait, and it never retries them: the
application's budget reservation and bounded retry are the only authority on
spend. Neither runs on a schedule or from a sensor that is on by default.
"""

import dagster as dg

from ..partitions import sources
from ..resources import LangGraph, Pipeline
from .snapshots import snapshot

PAID = {"link_lens/paid": "true"}


@dg.asset(
    partitions_def=sources,
    deps=[snapshot],
    group_name="review",
    pool="model_calls",
    tags=PAID,
)
def onboarding_request(
    context: dg.AssetExecutionContext, pipeline: Pipeline, langgraph: LangGraph
) -> dg.MaterializeResult:
    """Start an onboarding run for the source's latest snapshot, once.

    The graph proposes a mapping, with model calls inside the run's budget, and
    stops in the Agent Inbox for a person. Returns at once. A snapshot that
    already has a run is left with it.
    """
    result = pipeline.steps.request_onboarding(
        context.partition_key, langgraph.client()
    )
    if not result["started"]:
        context.log.info(
            "Snapshot already has run %s; nothing started.", result["run_id"]
        )
    return dg.MaterializeResult(
        metadata={
            "run_id": result["run_id"],
            "snapshot_id": result["snapshot_id"],
            "started_now": result["started"],
            "thread_id": result.get("thread_id", "existing"),
        }
    )


class CatalogueConfig(dg.Config):
    # Discovery ranks catalogue datasets with paid triage calls. Say so to run it.
    confirm_paid_calls: bool = False


@dg.asset(group_name="review", pool="model_calls", tags=PAID)
def source_catalogue(
    context: dg.AssetExecutionContext, config: CatalogueConfig, pipeline: Pipeline
) -> dg.MaterializeResult:
    """Discover and rank candidate datasets. Makes paid triage calls; never automatic."""
    if not config.confirm_paid_calls:
        raise dg.Failure(
            description=(
                "Discovery makes paid model calls. Launch it with "
                "confirm_paid_calls: true in the run configuration."
            ),
            allow_retries=False,
        )
    from link_lens import ingestion

    discovery = ingestion.discover()
    return dg.MaterializeResult(
        metadata={
            "discovery_id": str(discovery.get("id", "")),
            "shortlisted": len(discovery.get("shortlist", [])),
        }
    )
