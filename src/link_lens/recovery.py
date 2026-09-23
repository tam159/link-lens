"""Explicit replacement attempts; never mutate or approve the stopped attempt."""

from . import ingestion, store
from .settings import settings


def prepare_recovery(run_id, feedback):
    old = store.require("runs", run_id)
    if not feedback.strip():
        raise ValueError("Provide non-empty recovery feedback")
    if old.get("experiment_id", "terra-baseline") != settings().experiment_id:
        raise ValueError(
            "Select the predecessor's experiment in LINK_LENS_EXPERIMENT_ID"
        )
    if old.get("model") != settings().model:
        raise ValueError("Recovery must retain the predecessor's model")
    if old["status"] not in {"needs_review", "budget_exhausted", "failed"}:
        raise ValueError(
            "Only stopped needs_review, budget_exhausted or failed attempts can be recovered"
        )
    if old.get("final_validation", {}).get("passed") is False:
        raise ValueError("Final-test failures cannot be repaired through this command")
    for run in store.listing("runs"):
        if run.get("supersedes_run_id") == run_id:
            if run.get("carried_feedback") != feedback:
                raise ValueError(
                    "A replacement already exists with different feedback; inspect it first"
                )
            return run
    if not old.get("analysis_artifact") or not old.get("partitions_artifact"):
        raise ValueError(
            "Recovery requires a frozen reader and partitions; diagnose reader failures separately"
        )
    cursor = max(
        r.get("final_cursor", 0)
        for r in store.listing("runs")
        if r["snapshot_id"] == old["snapshot_id"]
    )
    pack = store.read_json(old["partitions_artifact"])
    if cursor >= len(pack["partitions"]["final"]):
        raise ValueError("No unused final-test records remain in this snapshot")
    run = ingestion.new_run(
        store.require("sources", old["source_id"]),
        store.require("snapshots", old["snapshot_id"]),
    )
    for field in (
        "analysis_artifact",
        "partitions_artifact",
        "partition_counts",
        "exploration_artifact",
        "mapping_id",
        "validation",
        "critique",
    ):
        if field in old:
            run[field] = old[field]
    run.update(
        supersedes_run_id=run_id,
        final_cursor=cursor,
        carried_feedback=feedback,
        recovery_requested_at=store.now(),
        recovery_requested_by=settings().reviewer,
        retry_reason="Explicit CLI recovery: new bounded attempt; predecessor costs and frozen evidence retained",
    )
    store.put("runs", run["id"], run, run["source_id"], "onboarding")
    return run
