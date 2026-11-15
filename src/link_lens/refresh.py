"""Keeping a registered source current: one function per step, with explicit IDs.

Each step takes the source it acts on, returns a small result record and writes
nothing new when it is repeated. An orchestrator calls these and holds no logic
of its own. None of them records a human decision: a mapping is approved in the
Agent Inbox, and a release is recorded with `link-lens release create`.

    check        download the source again; a snapshot is new only if the bytes are
    check_drift  compare a snapshot with the mapping approved for the source
    extract      extract a snapshot under that mapping, unless drift blocks it
    request_onboarding   start an onboarding run for a snapshot (model calls follow)
    assemble     assemble a batch from the approved runs of the registered sources
"""

import hashlib
import sys

from sqlalchemy import select, text

from . import drift, ingestion, sources, store
from .contracts import MappingSpec, SourceRequest, content_hash
from .extraction import extract as extract_rows
from .readers import read_records


class Blocked(ValueError):
    """The step ran and found something that stops it: no approval, or drift."""


def registered():
    """Refresh facts of every registered source."""
    return sources.state(kind="registered")


def check(source_id):
    """Download a source again and register a snapshot if its bytes changed.

    The publisher is recorded as checked either way. Makes no model call.
    """
    source = store.require("sources", source_id)
    before = sources.state(source_id)[0]["latest_snapshot_id"]
    resource_id = (
        store.require("snapshots", before).get("resource_id") if before else None
    )
    _, snapshot = ingestion.register(
        SourceRequest(
            dataset_id=source_id, portal=source["portal"], resource_id=resource_id
        )
    )
    return {
        "source_id": source_id,
        "snapshot_id": snapshot["id"],
        "previous_snapshot_id": before,
        "sha256": snapshot["sha256"],
        "changed": snapshot["id"] != before,
    }


def check_drift(source_id, snapshot_id=None):
    """Compare a snapshot (the latest by default) with the source's approved mapping."""
    state = sources.state(source_id)[0]
    snapshot_id = snapshot_id or state["latest_snapshot_id"]
    if snapshot_id is None:
        raise Blocked(f"sources/{source_id} has no snapshot")
    if state["approved_config_hash"] is None:
        # Nothing to compare with; not stored, because no mapping is in force.
        return {
            "source_id": source_id,
            "snapshot_id": snapshot_id,
            "config_hash": None,
            "status": "no_approved_mapping",
            "blocking": True,
            "reasons": [{"kind": "no_approved_mapping", "blocking": True}],
        }
    return drift.record(snapshot_id, state["approved_config_hash"])


def extract(source_id, snapshot_id=None, limit=None):
    """Extract a snapshot of a source under the mapping approved for that source.

    The latest snapshot by default; `limit` bounds the records read, and None
    reads every record the snapshot holds. Observations are keyed by content, so
    extracting the same snapshot again stores nothing. Raises `Blocked` when no
    mapping is approved or the snapshot's shape no longer fits the approved one.
    """
    from .db import onboarding

    checked = check_drift(source_id, snapshot_id)
    if checked["blocking"]:
        kinds = sorted({reason["kind"] for reason in checked["reasons"]})
        raise Blocked(
            f"sources/{source_id} snapshot {checked['snapshot_id'][:12]} cannot be "
            f"extracted: {', '.join(kinds)}"
        )
    config_hash = checked["config_hash"]
    with store.engine().connect() as connection:
        config = connection.execute(
            select(onboarding.mapping_config.c.config).where(
                onboarding.mapping_config.c.config_hash == config_hash
            )
        ).scalar_one()
    if content_hash(config) != config_hash:
        raise Blocked("The stored mapping config does not match its approved hash")
    spec = MappingSpec.model_validate(config)
    snapshot = store.require("snapshots", checked["snapshot_id"])
    _, rows = read_records(
        store.blob_path(snapshot["artifact_id"]),
        spec.reader,
        snapshot["sha256"],
        snapshot.get("receipt", {}).get("partial", False),
        sys.maxsize if limit is None else limit,
    )
    result = extract_rows(spec, rows, snapshot)
    ids = sorted(observation["id"] for observation in result["observations"])
    return {
        "source_id": source_id,
        "snapshot_id": snapshot["id"],
        "config_hash": config_hash,
        "records": len(rows),
        "observations": len(ids),
        "inserted": store.put_observations(result["observations"]),
        "issues": len(result["issues"]),
        "observation_digest": hashlib.sha256("".join(ids).encode()).hexdigest(),
    }


def start_thread(run, client):
    """Start the onboarding graph for a run on the LangGraph server.

    Returns at once; the graph makes model calls within the run's budget and
    stops at the Agent Inbox for a person's review.
    """
    if run.get("thread_id"):
        raise ValueError(
            "This run already has a thread; review or inspect it instead of duplicating execution"
        )
    thread = client.threads.create(
        metadata={
            "application": "link-lens",
            "onboarding_run_id": run["id"],
            "source": run["source_slug"],
        }
    )
    run["thread_id"] = thread["thread_id"]
    store.put("runs", run["id"], run, run["source_id"], "onboarding")
    started = client.runs.create(
        thread["thread_id"],
        "onboard",
        input={"run_id": run["id"], "feedback": run.get("carried_feedback", "none")},
        config={"recursion_limit": 40},
    )
    return {
        "run_id": run["id"],
        "thread_id": thread["thread_id"],
        "server_run_id": started["run_id"],
    }


def request_onboarding(source_id, client, snapshot_id=None):
    """Start an onboarding run for a snapshot of a source, once.

    A snapshot that already has an onboarding run which has not failed is left
    with it: asking again starts nothing and spends nothing.
    """
    snapshot_id = snapshot_id or sources.state(source_id)[0]["latest_snapshot_id"]
    if snapshot_id is None:
        raise Blocked(f"sources/{source_id} has no snapshot")
    with store.engine().connect() as connection:
        existing = connection.execute(
            text(
                "SELECT id, status FROM onboarding.run WHERE snapshot_id = :snapshot "
                "AND kind = 'onboarding' AND coalesce(status, '') <> 'failed' "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"snapshot": snapshot_id},
        ).first()
    if existing is not None:
        return {
            "source_id": source_id,
            "snapshot_id": snapshot_id,
            "run_id": existing.id,
            "run_status": existing.status,
            "started": False,
        }
    run = ingestion.new_run(
        store.require("sources", source_id), store.require("snapshots", snapshot_id)
    )
    return {
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        **start_thread(run, client),
        "started": True,
    }


def approved_runs():
    """The approved run in force of each registered source that has one."""
    return [
        state["approved_run_id"]
        for state in registered()
        if state["approved_run_id"]
        and store.require("runs", state["approved_run_id"]).get("status") == "completed"
    ]


def assemble(
    run_ids=None, minimum_profiles=50, cohort_pool_size=None, baseline_batch_id=None
):
    """Assemble a batch of entities, links and profiles. Deterministic; no model call.

    From the approved runs of the registered sources unless `run_ids` are given.
    Every call makes a new batch; a batch is never rewritten, and no batch is
    served until a person records a release of it.
    """
    from . import pipeline

    run_ids = list(run_ids or approved_runs())
    if not run_ids:
        raise Blocked("No registered source has an approved, completed run")
    batch = pipeline.assemble(
        run_ids, minimum_profiles, cohort_pool_size, baseline_batch_id
    )
    with store.engine().connect() as connection:
        versions = (
            connection.execute(
                text(
                    "SELECT sha256_hex(profile_version) FROM identity.profile "
                    "WHERE batch_id = :batch ORDER BY 1"
                ),
                {"batch": batch["id"]},
            )
            .scalars()
            .all()
        )
    return {
        "batch_id": batch["id"],
        "run_ids": run_ids,
        "counts": batch["counts"],
        "profile_versions": len(versions),
        "profile_digest": hashlib.sha256("".join(versions).encode()).hexdigest(),
    }
