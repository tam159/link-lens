"""Sensors: Dagster reacts to rows people and steps recorded. It never writes one.

Each sensor remembers the last row it saw and starts from the present the first
time it runs, so turning one on does not replay history.

    registered_sources   keeps the source partitions equal to the registered sources
    mapping_approved     a new approval requests extraction for that source
    release_recorded     a new release requests a build of the dbt models and their tests
    ontology_promoted    a promotion is reported and triggers nothing
    drift_detected       blocking drift requests onboarding; off unless someone turns it on,
                         because onboarding makes model calls
"""

import json

import dagster as dg
from sqlalchemy import text

from .partitions import sources


def rows(sql, **parameters):
    from link_lens import store

    with store.engine().connect() as connection:
        return [
            dict(row) for row in connection.execute(text(sql), parameters).mappings()
        ]


BEFORE_ANY_ROW = {"at": "0001-01-01T00:00:00+00:00", "id": ""}
BEFORE_ANY_ID = {"id": 0}


def since(context, latest_sql, empty):
    """The cursor as a mapping, or None the first time, when the present is recorded.

    `latest_sql` selects the newest row's cursor; `empty` is the cursor to keep
    when the table has no row yet.
    """
    if context.cursor:
        return json.loads(context.cursor)
    latest = rows(latest_sql)
    context.update_cursor(json.dumps(latest[0] if latest else empty, default=str))
    return None


@dg.sensor(
    name="registered_sources",
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Adds a partition for every registered source that has none.",
)
def registered_sources(context: dg.SensorEvaluationContext):
    from link_lens import refresh

    registered = {state["source_id"] for state in refresh.registered()}
    missing = sorted(
        registered - set(context.instance.get_dynamic_partitions(sources.name))
    )
    if not missing:
        return dg.SkipReason(
            f"All {len(registered)} registered sources have a partition."
        )
    return dg.SensorResult(
        dynamic_partitions_requests=[sources.build_add_request(missing)]
    )


def approval_sensor(job):
    @dg.sensor(
        name="mapping_approved",
        job=job,
        minimum_interval_seconds=30,
        default_status=dg.DefaultSensorStatus.RUNNING,
        description="A mapping a person approved requests extraction for its source.",
    )
    def mapping_approved(context: dg.SensorEvaluationContext):
        latest = (
            "SELECT created_at::text AS at, id FROM onboarding.approval "
            "ORDER BY created_at DESC, id DESC LIMIT 1"
        )
        cursor = since(context, latest, BEFORE_ANY_ROW)
        if cursor is None:
            return dg.SkipReason(
                "First run: starting from the approvals recorded so far."
            )
        approved = rows(
            "SELECT a.id, a.created_at::text AS at, a.decision, r.source_id, s.kind "
            "FROM onboarding.approval a "
            "LEFT JOIN onboarding.run r ON r.id = a.run_id "
            "LEFT JOIN catalog.source s ON s.id = r.source_id "
            "WHERE (a.created_at, a.id) > (CAST(:at AS timestamptz), :id) "
            "ORDER BY a.created_at, a.id LIMIT 100",
            **cursor,
        )
        if not approved:
            return dg.SkipReason("No new approval.")
        wanted = [
            row
            for row in approved
            if row["decision"] == "approved" and row["kind"] == "registered"
        ]
        known = set(context.instance.get_dynamic_partitions(sources.name))
        new = sorted({row["source_id"] for row in wanted} - known)
        return dg.SensorResult(
            run_requests=[
                dg.RunRequest(
                    run_key=f"approval-{row['id']}",
                    partition_key=row["source_id"],
                    tags={"link_lens/approval": row["id"]},
                )
                for row in wanted
            ],
            dynamic_partitions_requests=[sources.build_add_request(new)] if new else [],
            cursor=json.dumps({"at": approved[-1]["at"], "id": approved[-1]["id"]}),
        )

    return mapping_approved


def release_sensor(job):
    @dg.sensor(
        name="release_recorded",
        job=job,
        minimum_interval_seconds=30,
        default_status=dg.DefaultSensorStatus.RUNNING,
        description=(
            "A release a person recorded requests a build of the dbt models and their "
            "tests. The release's OKF tree and its bundles are built by the release "
            "command itself."
        ),
    )
    def release_recorded(context: dg.SensorEvaluationContext):
        cursor = since(
            context,
            "SELECT id FROM ops.release ORDER BY id DESC LIMIT 1",
            BEFORE_ANY_ID,
        )
        if cursor is None:
            return dg.SkipReason(
                "First run: starting from the releases recorded so far."
            )
        released = rows(
            "SELECT id, batch_id, released_by FROM ops.release WHERE id > :id ORDER BY id",
            id=int(cursor["id"] or 0),
        )
        if not released:
            return dg.SkipReason("No new release.")
        return dg.SensorResult(
            run_requests=[
                dg.RunRequest(
                    run_key=f"release-{row['id']}",
                    tags={
                        "link_lens/release": str(row["id"]),
                        "link_lens/batch": row["batch_id"],
                    },
                )
                for row in released
            ],
            cursor=json.dumps({"id": released[-1]["id"]}),
        )

    return release_recorded


@dg.sensor(
    name="ontology_promoted",
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Reports an ontology version a person promoted. It triggers nothing.",
)
def ontology_promoted(context: dg.SensorEvaluationContext):
    cursor = since(
        context,
        "SELECT id FROM ontology.activation ORDER BY id DESC LIMIT 1",
        BEFORE_ANY_ID,
    )
    if cursor is None:
        return dg.SkipReason(
            "First run: starting from the activations recorded so far."
        )
    promoted = rows(
        "SELECT id, experiment_id, sha256_hex(version_hash) AS version, reviewer "
        "FROM ontology.activation WHERE id > :id AND status = 'promoted' ORDER BY id",
        id=int(cursor["id"] or 0),
    )
    if not promoted:
        return dg.SkipReason("No new promotion.")
    context.update_cursor(json.dumps({"id": promoted[-1]["id"]}))
    for row in promoted:
        context.log.info(
            "Ontology %s promoted for %s by %s. Existing mappings keep the version "
            "they were approved under; nothing is rebuilt.",
            row["version"][:12],
            row["experiment_id"],
            row["reviewer"],
        )
    return dg.SkipReason(
        f"{len(promoted)} promotion(s) reported, latest {promoted[-1]['version'][:12]}. "
        "A promotion triggers nothing by itself."
    )


def drift_sensor(job):
    @dg.sensor(
        name="drift_detected",
        job=job,
        minimum_interval_seconds=60,
        # Onboarding makes model calls. A person turns this on, or requests
        # onboarding for a drifted source by hand.
        default_status=dg.DefaultSensorStatus.STOPPED,
        description=(
            "A snapshot the approved mapping cannot read requests an onboarding run "
            "for its source. Off by default: onboarding spends on model calls."
        ),
    )
    def drift_detected(context: dg.SensorEvaluationContext):
        latest = (
            "SELECT checked_at::text AS at, snapshot_id AS id FROM catalog.drift_check "
            "ORDER BY checked_at DESC, snapshot_id DESC LIMIT 1"
        )
        cursor = since(context, latest, BEFORE_ANY_ROW)
        if cursor is None:
            return dg.SkipReason(
                "First run: starting from the drift checks recorded so far."
            )
        checks = rows(
            "SELECT checked_at::text AS at, snapshot_id AS id, source_id, blocking, "
            "sha256_hex(config_hash) AS config FROM catalog.drift_check "
            "WHERE (checked_at, snapshot_id) > (CAST(:at AS timestamptz), :id) "
            "ORDER BY checked_at, snapshot_id LIMIT 100",
            **cursor,
        )
        if not checks:
            return dg.SkipReason("No new drift check.")
        return dg.SensorResult(
            run_requests=[
                dg.RunRequest(
                    run_key=f"drift-{row['id']}-{row['config'][:12]}",
                    partition_key=row["source_id"],
                    tags={"link_lens/snapshot": row["id"], "link_lens/paid": "true"},
                )
                for row in checks
                if row["blocking"]
            ],
            cursor=json.dumps({"at": checks[-1]["at"], "id": checks[-1]["id"]}),
        )

    return drift_detected
