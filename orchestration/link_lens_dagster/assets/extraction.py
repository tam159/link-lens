"""Observations of a source, extracted under its approved mapping."""

import dagster as dg

from ..partitions import sources
from ..resources import Pipeline
from .snapshots import RETRY, snapshot


class ExtractionConfig(dg.Config):
    # Records to read from the snapshot; unset reads every record it holds.
    record_limit: int | None = None


@dg.asset(
    partitions_def=sources,
    deps=[snapshot],
    group_name="sources",
    pool="database",
    retry_policy=RETRY,
    check_specs=[
        dg.AssetCheckSpec(
            "observations_have_records",
            asset="observations",
            description="Every observation of the source points at a stored source record.",
        ),
        dg.AssetCheckSpec(
            "extraction_is_complete",
            asset="observations",
            description="Every observation just extracted is stored.",
        ),
    ],
)
def observations(
    context: dg.AssetExecutionContext, config: ExtractionConfig, pipeline: Pipeline
):
    """Extract the source's latest snapshot with the shared declarative engine.

    Runs only under a mapping a person approved, and not when the snapshot's
    shape has drifted from it. Observations are keyed by content, so extracting
    an unchanged snapshot stores nothing. No model call.
    """
    from link_lens.refresh import Blocked

    source_id = context.partition_key
    try:
        result = pipeline.steps.extract(source_id, limit=config.record_limit)
    except Blocked as blocked:
        # Waiting for a person; retrying cannot help.
        raise dg.Failure(description=str(blocked), allow_retries=False) from blocked
    yield dg.MaterializeResult(
        data_version=dg.DataVersion(result["observation_digest"]),
        metadata={
            "snapshot_id": result["snapshot_id"],
            "config_hash": result["config_hash"],
            "records": result["records"],
            "observations": result["observations"],
            "repeated_in_snapshot": result["repeated_in_snapshot"],
            "newly_stored": result["inserted"],
            "issues": result["issues"],
            "observation_digest": result["observation_digest"],
        },
    )
    orphans = pipeline.scalar(
        "SELECT count(*) FROM evidence.observation o WHERE o.source_id = :source "
        "AND NOT EXISTS (SELECT 1 FROM evidence.source_record r "
        "WHERE r.source_id = o.source_id AND r.id = o.record_id)",
        source=source_id,
    )
    yield dg.AssetCheckResult(
        check_name="observations_have_records",
        passed=orphans == 0,
        metadata={"observations_without_a_record": orphans},
    )
    stored = pipeline.scalar(
        "SELECT count(*) FROM evidence.observation o "
        "JOIN evidence.source_record r ON r.source_id = o.source_id AND r.id = o.record_id "
        "WHERE o.source_id = :source AND r.snapshot_id = :snapshot "
        "AND o.config_hash = sha256_from_hex(:config)",
        source=source_id,
        snapshot=result["snapshot_id"],
        config=result["config_hash"],
    )
    yield dg.AssetCheckResult(
        check_name="extraction_is_complete",
        passed=stored >= result["observations"],
        metadata={"extracted": result["observations"], "stored_for_snapshot": stored},
    )
