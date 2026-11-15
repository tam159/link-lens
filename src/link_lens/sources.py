"""Refresh facts of a source: cadence, last check, last change, mapping in force.

Each function takes the source it acts on and returns a small record. An
orchestrator reads `state` to decide what is due and keeps no copy of its own.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert

from . import store
from .db import catalog
from .db.records import parse_time, render_time


def record_check(source_id, checked_at=None):
    """Note that the publisher was checked for new data, changed or not.

    Recording the same or an earlier time again changes nothing.
    """
    at = parse_time(checked_at) if isinstance(checked_at, str) else checked_at
    at = at or datetime.now(UTC)
    refresh = catalog.source_refresh
    statement = insert(refresh).values(source_id=source_id, last_checked_at=at)
    with store.engine().begin() as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["source_id"],
                set_={
                    "last_checked_at": func.greatest(
                        refresh.c.last_checked_at, statement.excluded.last_checked_at
                    ),
                    # The publisher answered: whatever failed before is over.
                    "consecutive_failures": 0,
                    "updated_at": func.now(),
                },
                where=refresh.c.last_checked_at.is_distinct_from(
                    func.greatest(
                        refresh.c.last_checked_at, statement.excluded.last_checked_at
                    )
                )
                | (refresh.c.consecutive_failures > 0),
            )
        )
    return state(source_id)[0]


def set_cadence(source_id, days):
    """Set how often the source should be checked; `None` clears the cadence."""
    cadence = None if days is None else timedelta(days=days)
    if cadence is not None and cadence <= timedelta(0):
        raise ValueError("A cadence must be longer than zero")
    refresh = catalog.source_refresh
    statement = insert(refresh).values(source_id=source_id, cadence=cadence)
    with store.engine().begin() as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["source_id"],
                set_={"cadence": cadence, "updated_at": func.now()},
                where=refresh.c.cadence.is_distinct_from(cadence),
            )
        )
    return state(source_id)[0]


def state(source_id=None, kind=None):
    """Refresh facts per source, as `catalog.source_state` reports them."""
    view = text(
        "SELECT * FROM catalog.source_state "
        "WHERE (CAST(:source AS text) IS NULL OR source_id = :source) "
        "AND (CAST(:kind AS text) IS NULL OR kind = :kind) ORDER BY source_id"
    )
    with store.engine().connect() as connection:
        rows = connection.execute(view, {"source": source_id, "kind": kind}).mappings()
        result = [
            {
                **row,
                "cadence_days": None
                if row["cadence"] is None
                else row["cadence"].total_seconds() / 86400,
                "approved_config_hash": None
                if row["approved_config_hash"] is None
                else bytes(row["approved_config_hash"]).hex(),
                **{
                    key: None if row[key] is None else render_time(row[key])
                    for key in (
                        "last_checked_at",
                        "next_check_due_at",
                        "last_changed_at",
                        "approved_at",
                        "paused_at",
                        "last_failure_at",
                        "retry_after",
                    )
                },
            }
            for row in rows
        ]
    for row in result:
        del row["cadence"]
    if source_id is not None and not result:
        raise KeyError(f"sources/{source_id} not found")
    return result


def record_failure(source_id, error, failed_at=None):
    """Note that a check of the publisher failed. The next attempt waits longer each time."""
    at = parse_time(failed_at) if isinstance(failed_at, str) else failed_at
    at = at or datetime.now(UTC)
    refresh = catalog.source_refresh
    statement = insert(refresh).values(
        source_id=source_id,
        consecutive_failures=1,
        last_failure_at=at,
        last_error=str(error)[:400],
    )
    with store.engine().begin() as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["source_id"],
                set_={
                    "consecutive_failures": refresh.c.consecutive_failures + 1,
                    "last_failure_at": at,
                    "last_error": str(error)[:400],
                    "updated_at": func.now(),
                },
            )
        )
    return state(source_id)[0]


def pause(source_id, by):
    """Stop scheduled checks of a source until it is resumed. A person's decision."""
    if not by or not by.strip():
        raise ValueError("Pausing a source needs the name of the person pausing it")
    refresh = catalog.source_refresh
    statement = insert(refresh).values(
        source_id=source_id, paused_at=func.now(), paused_by=by.strip()
    )
    with store.engine().begin() as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["source_id"],
                set_={
                    "paused_at": func.now(),
                    "paused_by": by.strip(),
                    "updated_at": func.now(),
                },
                where=refresh.c.paused_at.is_(None),
            )
        )
    return state(source_id)[0]


def resume(source_id):
    """Let scheduled checks of a paused source start again."""
    refresh = catalog.source_refresh
    with store.engine().begin() as connection:
        connection.execute(
            refresh.update()
            .where(refresh.c.source_id == source_id, refresh.c.paused_at.is_not(None))
            .values(paused_at=None, paused_by=None, updated_at=func.now())
        )
    return state(source_id)[0]


def due(now=None, limit=None, per_host=None):
    """Registered sources whose next check is due, most overdue first.

    A source is due when it has a cadence, an approved mapping to extract with,
    is not paused, has never been checked or its last check plus cadence has
    passed, and is not waiting out a failure. `per_host` caps how many sources
    of one publisher portal are returned, so a schedule cannot ask one host for
    everything at once; `limit` caps the whole answer.
    """
    at = parse_time(now) if isinstance(now, str) else now
    at = at or datetime.now(UTC)
    query = text(
        "SELECT state.source_id, state.next_check_due_at, state.last_checked_at, "
        "state.consecutive_failures, "
        "substring(source.portal from '://([^/]+)') AS host "
        "FROM catalog.source_state state "
        "JOIN catalog.source source ON source.id = state.source_id "
        "WHERE state.kind = 'registered' AND state.cadence IS NOT NULL "
        "AND state.approved_config_hash IS NOT NULL AND state.paused_at IS NULL "
        "AND (state.last_checked_at IS NULL OR state.next_check_due_at <= :now) "
        "AND (state.retry_after IS NULL OR state.retry_after <= :now) "
        "ORDER BY state.next_check_due_at NULLS FIRST, state.source_id"
    )
    with store.engine().connect() as connection:
        found = connection.execute(query, {"now": at}).mappings().all()
    taken, chosen = {}, []
    for row in found:
        host = row["host"] or ""
        if per_host is not None and taken.get(host, 0) >= per_host:
            continue
        taken[host] = taken.get(host, 0) + 1
        chosen.append(
            {
                "source_id": row["source_id"],
                "host": host,
                # How many checks have failed in a row before this one.
                "attempt": row["consecutive_failures"],
                "due_at": None
                if row["next_check_due_at"] is None
                else render_time(row["next_check_due_at"]),
            }
        )
        if limit is not None and len(chosen) >= limit:
            break
    return chosen


def overdue(now=None, grace=timedelta(hours=1)):
    """Registered sources that should have been checked by now and were not, with why.

    Overdue by more than `grace`, or failing three times in a row. A paused
    source and one without a cadence are not overdue: someone decided that.
    """
    at = parse_time(now) if isinstance(now, str) else now
    at = at or datetime.now(UTC)
    query = text(
        "SELECT source_id, title, next_check_due_at, consecutive_failures, last_error "
        "FROM catalog.source_state "
        "WHERE kind = 'registered' AND cadence IS NOT NULL AND paused_at IS NULL "
        "AND approved_config_hash IS NOT NULL "
        "AND ((last_checked_at IS NULL AND consecutive_failures > 0) "
        "  OR next_check_due_at + :grace < :now OR consecutive_failures >= 3) "
        "ORDER BY next_check_due_at NULLS FIRST, source_id"
    )
    with store.engine().connect() as connection:
        found = connection.execute(query, {"now": at, "grace": grace}).mappings().all()
    return [
        {
            "source_id": row["source_id"],
            "title": row["title"],
            "due_at": None
            if row["next_check_due_at"] is None
            else render_time(row["next_check_due_at"]),
            "consecutive_failures": row["consecutive_failures"],
            "reason": (
                f"{row['consecutive_failures']} checks failed in a row: {row['last_error']}"
                if row["consecutive_failures"]
                else "not checked since it became due"
            ),
        }
        for row in found
    ]
