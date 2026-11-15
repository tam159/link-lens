"""Alerts: the team hears about a problem without watching a screen.

Each sensor sends one line through `link_lens.alerts`, naming the source and
linking to where to look. Without a webhook configured an alert is logged and
the sensor still moves on, so configuring one later does not replay old news.

    alert_run_failed        a run failed
    alert_check_failed      a run succeeded but one of its checks did not pass
    alert_drift             a snapshot the approved mapping cannot read
    alert_overdue_sources   a source overdue for its check, or failing
    alert_budget            the experiment's model budget is nearly or fully spent
"""

import json

import dagster as dg

from .sensors import BEFORE_ANY_ROW, rows, since

BUDGET_LEVELS = (0.8, 1.0)


def links():
    from link_lens.settings import settings

    return settings().dagster_url.rstrip("/"), settings().inbox_url.rstrip("/")


def title_of(source_id):
    if not source_id:
        return None
    found = rows("SELECT title FROM catalog.source WHERE id = :id", id=source_id)
    return f"{found[0]['title'] or source_id} ({source_id})" if found else source_id


def failed_checks(instance, run_id):
    """Names of the checks that did not pass in a run, as asset:check."""
    names = []
    for entry in instance.all_logs(
        run_id, of_type=dg.DagsterEventType.ASSET_CHECK_EVALUATION
    ):
        evaluation = entry.dagster_event.event_specific_data
        if not evaluation.passed:
            names.append(
                f"{evaluation.asset_key.to_user_string()}:{evaluation.check_name}"
            )
    return sorted(set(names))


@dg.run_failure_sensor(
    name="alert_run_failed",
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Tells the team when a run fails, with the source and a link to the run.",
)
def alert_run_failed(context: dg.RunFailureSensorContext):
    from link_lens import alerts

    run = context.dagster_run
    dagster_url, _ = links()
    details = {"Error": (context.failure_event.message or "")[:300]}
    checks = failed_checks(context.instance, run.run_id)
    if checks:
        details["Failed checks"] = ", ".join(checks)
    alerts.send(
        "run_failed",
        f"{run.job_name} failed",
        source=title_of(run.tags.get("dagster/partition")),
        link=f"{dagster_url}/runs/{run.run_id}",
        details=details,
    )


@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.SUCCESS,
    name="alert_check_failed",
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Tells the team when a run finished but a check in it did not pass.",
)
def alert_check_failed(context: dg.RunStatusSensorContext):
    from link_lens import alerts

    run = context.dagster_run
    checks = failed_checks(context.instance, run.run_id)
    if not checks:
        return
    dagster_url, _ = links()
    alerts.send(
        "check_failed",
        ", ".join(checks),
        source=title_of(run.tags.get("dagster/partition")),
        link=f"{dagster_url}/runs/{run.run_id}",
        details={"Job": run.job_name},
    )


@dg.sensor(
    name="alert_drift",
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Tells the team when a snapshot no longer fits its source's approved mapping.",
)
def alert_drift(context: dg.SensorEvaluationContext):
    from link_lens import alerts

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
        "SELECT checked_at::text AS at, snapshot_id AS id, source_id, blocking, reasons "
        "FROM catalog.drift_check "
        "WHERE (checked_at, snapshot_id) > (CAST(:at AS timestamptz), :id) "
        "ORDER BY checked_at, snapshot_id LIMIT 100",
        **cursor,
    )
    if not checks:
        return dg.SkipReason("No new drift check.")
    dagster_url, inbox_url = links()
    sent = 0
    for row in checks:
        if not row["blocking"]:
            continue
        reasons = [
            reason["kind"] + (f" {reason['column']}" if reason.get("column") else "")
            for reason in row["reasons"]
            if reason.get("blocking")
        ]
        alerts.send(
            "drift",
            "the approved mapping cannot read the new snapshot; a person must review a new one",
            source=title_of(row["source_id"]),
            link=f"{dagster_url}/assets/snapshot?partition={row['source_id']}",
            details={"Reasons": "; ".join(reasons)[:300], "Review": inbox_url},
        )
        sent += 1
    context.update_cursor(json.dumps({"at": checks[-1]["at"], "id": checks[-1]["id"]}))
    return dg.SkipReason(f"{sent} drift alert(s) for {len(checks)} new check(s).")


@dg.sensor(
    name="alert_overdue_sources",
    minimum_interval_seconds=1800,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Tells the team once when a source becomes overdue for its check or keeps failing.",
)
def alert_overdue_sources(context: dg.SensorEvaluationContext):
    from link_lens import alerts, sources

    late = sources.overdue()
    told = set(json.loads(context.cursor)) if context.cursor else set()
    dagster_url, _ = links()
    now_late = set()
    sent = 0
    for row in late:
        failing = row["consecutive_failures"] >= 3
        key = f"{row['source_id']}|{row['due_at']}|{'failing' if failing else 'late'}"
        now_late.add(key)
        if key in told:
            continue
        alerts.send(
            "stale_source",
            row["reason"],
            source=f"{row['title'] or row['source_id']} ({row['source_id']})",
            link=f"{dagster_url}/assets/snapshot?partition={row['source_id']}",
            details={"Due": row["due_at"] or "never checked"},
        )
        sent += 1
    # Only what is late now is remembered: a source that recovers and falls
    # behind again is reported again.
    context.update_cursor(json.dumps(sorted(now_late)))
    return dg.SkipReason(
        f"{len(late)} source(s) overdue or failing; {sent} newly reported."
    )


@dg.sensor(
    name="alert_budget",
    minimum_interval_seconds=300,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Tells the team when 80% and when all of the experiment's model budget is spent.",
)
def alert_budget(context: dg.SensorEvaluationContext):
    from link_lens import alerts, budget
    from link_lens.settings import settings

    experiment = settings().experiment_id
    summary = budget.summary(experiment)
    cap, charged = summary["cap_usd"], summary["charged_usd"]
    share = charged / cap if cap else 0.0
    cursor = json.loads(context.cursor) if context.cursor else {}
    told = cursor.get("level", 0.0) if cursor.get("experiment") == experiment else 0.0
    reached = max((level for level in BUDGET_LEVELS if share >= level), default=0.0)
    if reached > told:
        alerts.send(
            "budget",
            (
                "the cap is reached; paid steps will be refused"
                if reached >= 1.0
                else f"{share:.0%} of the cap is spent"
            ),
            details={
                "Experiment": experiment,
                "Charged": f"USD {charged:.4f} of {cap:.2f}",
                "Basis": summary.get("basis", ""),
            },
        )
    context.update_cursor(
        json.dumps({"experiment": experiment, "level": max(reached, told)})
    )
    return dg.SkipReason(f"{share:.0%} of the budget of {experiment} is charged.")
