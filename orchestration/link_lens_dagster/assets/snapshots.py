"""A source's latest snapshot, and whether it still fits the approved mapping."""

import dagster as dg

from ..partitions import sources
from ..resources import Pipeline

# Deterministic steps may be retried: they write nothing twice.
RETRY = dg.RetryPolicy(max_retries=2, delay=30, backoff=dg.Backoff.EXPONENTIAL)


class SnapshotConfig(dg.Config):
    # Emit the snapshot even when the bytes did not change, to run what follows.
    force: bool = False


@dg.asset(
    partitions_def=sources,
    group_name="sources",
    pool="downloads",
    retry_policy=RETRY,
    output_required=False,
    check_specs=[
        dg.AssetCheckSpec(
            "schema_drift",
            asset="snapshot",
            blocking=True,
            description=(
                "The snapshot's format and columns still fit the mapping approved "
                "for the source. A failure stops extraction until a person approves "
                "a mapping for the new shape."
            ),
        )
    ],
)
def snapshot(
    context: dg.AssetExecutionContext, config: SnapshotConfig, pipeline: Pipeline
):
    """Download the source again. A snapshot is new only when the bytes are.

    When they are not, nothing is emitted and nothing downstream runs. The
    publisher is recorded as checked either way. No model call.
    """
    source_id = context.partition_key
    checked = pipeline.steps.check(source_id)
    drift = pipeline.steps.check_drift(source_id, checked["snapshot_id"])
    if checked["changed"] or config.force:
        yield dg.Output(
            checked["snapshot_id"],
            data_version=dg.DataVersion(checked["sha256"]),
            metadata={
                "snapshot_id": checked["snapshot_id"],
                "sha256": checked["sha256"],
                "previous_snapshot_id": checked["previous_snapshot_id"] or "none",
                "bytes_changed": checked["changed"],
            },
        )
    else:
        context.log.info(
            "Bytes unchanged since snapshot %s; nothing to do.", checked["snapshot_id"]
        )
    yield dg.AssetCheckResult(
        passed=not drift["blocking"],
        severity=dg.AssetCheckSeverity.ERROR,
        description=(
            "No approved mapping fits this snapshot."
            if drift["blocking"]
            else f"Shape is {drift['status']} against the approved mapping."
        ),
        metadata={
            "status": drift["status"],
            "blocking": drift["blocking"],
            "reasons": dg.MetadataValue.json(drift["reasons"]),
            "snapshot_id": checked["snapshot_id"],
            "config_hash": drift["config_hash"] or "none",
        },
    )
