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
                    "updated_at": func.now(),
                },
                where=refresh.c.last_checked_at.is_distinct_from(
                    func.greatest(
                        refresh.c.last_checked_at, statement.excluded.last_checked_at
                    )
                ),
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
