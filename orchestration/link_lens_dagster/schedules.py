"""Schedules. Cadence is data in the source registry; a schedule only asks what is due.

    due_sources               every 15 minutes: refresh the sources whose check is due
    check_source_freshness    hourly: is any source overdue or failing?
    weekly_batch              assemble a batch; off until someone turns it on
    prune_run_history         daily: delete Dagster's own old runs

There is one schedule for all sources, not one per source: thousands of
schedules would be thousands of things to keep in step with the registry.
"""

from datetime import UTC, datetime, timedelta

import dagster as dg

from .assets.snapshots import snapshot
from .partitions import sources as source_partitions
from .resources import Pipeline

# How many refreshes one evaluation may start, in all and for one publisher's
# portal, so that a backlog is worked off without leaning on any host.
MAX_PER_TICK = 50
MAX_PER_HOST = 5


def due_sources_schedule(job):
    @dg.schedule(
        name="due_sources",
        cron_schedule="*/15 * * * *",
        execution_timezone="UTC",
        job=job,
        default_status=dg.DefaultScheduleStatus.RUNNING,
        description=(
            "Refreshes each registered source whose check is due by its cadence. "
            "A source with no cadence, a paused source and one waiting out a "
            "failure are left alone."
        ),
    )
    def due_sources(context: dg.ScheduleEvaluationContext):
        from link_lens import sources

        now = context.scheduled_execution_time or datetime.now(UTC)
        due = sources.due(now, limit=MAX_PER_TICK, per_host=MAX_PER_HOST)
        known = set(context.instance.get_dynamic_partitions(source_partitions.name))
        wanted = [row for row in due if row["source_id"] in known]
        if not wanted:
            return dg.SkipReason(
                "No source is due."
                if not due
                else f"{len(due)} due source(s) have no partition yet."
            )
        return [
            dg.RunRequest(
                # One run per source, due time and attempt: asked for again
                # while it is queued, nothing more starts; after a failure and
                # its wait, the next attempt is a new run.
                run_key=f"refresh-{row['source_id']}-{row['due_at'] or 'first'}-{row['attempt']}",
                partition_key=row["source_id"],
                tags={"link_lens/due_at": row["due_at"] or "never checked"},
            )
            for row in wanted
        ]

    return due_sources


@dg.asset_check(
    asset=snapshot,
    name="sources_checked_on_time",
    description=(
        "No registered source is overdue for its check by more than an hour or "
        "has failed three checks in a row. Lateness is worked out from each "
        "source's cadence in the registry."
    ),
)
def sources_checked_on_time(pipeline: Pipeline) -> dg.AssetCheckResult:
    from link_lens import sources

    late = sources.overdue()
    return dg.AssetCheckResult(
        passed=not late,
        severity=dg.AssetCheckSeverity.WARN,
        description=(
            f"{len(late)} source(s) overdue or failing."
            if late
            else "Every source is on time."
        ),
        metadata={
            "overdue_or_failing": len(late),
            "sources": dg.MetadataValue.json(late[:50]),
        },
    )


check_source_freshness = dg.define_asset_job(
    "check_source_freshness",
    selection=dg.AssetSelection.checks(sources_checked_on_time),
    description="Ask whether any source is overdue or failing.",
)

freshness_schedule = dg.ScheduleDefinition(
    name="check_source_freshness_hourly",
    cron_schedule="5 * * * *",
    execution_timezone="UTC",
    job=check_source_freshness,
    default_status=dg.DefaultScheduleStatus.RUNNING,
)


def weekly_batch_schedule(job):
    return dg.ScheduleDefinition(
        name="weekly_batch",
        cron_schedule="0 3 * * 1",
        execution_timezone="UTC",
        job=job,
        # A batch after a refresh also changes by resampling (plan, phase D3a),
        # and a batch serves nobody until a person releases it. Someone turns
        # this on when a weekly batch is wanted.
        default_status=dg.DefaultScheduleStatus.STOPPED,
        description="Assemble a new batch from the current run of every registered source.",
    )


class RetentionConfig(dg.Config):
    keep_days: int = 90


@dg.op
def delete_old_runs(context: dg.OpExecutionContext, config: RetentionConfig) -> int:
    """Delete finished runs older than `keep_days` from Dagster's own storage.

    This is run history only. Nothing of the application's is in that database.
    """
    cutoff = datetime.now(UTC) - timedelta(days=config.keep_days)
    finished = [
        dg.DagsterRunStatus.SUCCESS,
        dg.DagsterRunStatus.FAILURE,
        dg.DagsterRunStatus.CANCELED,
    ]
    deleted = 0
    while True:
        old = context.instance.get_run_records(
            filters=dg.RunsFilter(created_before=cutoff, statuses=finished), limit=200
        )
        if not old:
            break
        for record in old:
            context.instance.delete_run(record.dagster_run.run_id)
            deleted += 1
    context.log.info("Deleted %s run(s) created before %s.", deleted, cutoff.date())
    return deleted


@dg.job(
    description="Delete Dagster's own finished runs older than the retention period."
)
def prune_run_history():
    delete_old_runs()


retention_schedule = dg.ScheduleDefinition(
    name="prune_run_history_daily",
    cron_schedule="30 2 * * *",
    execution_timezone="UTC",
    job=prune_run_history,
    default_status=dg.DefaultScheduleStatus.RUNNING,
)
