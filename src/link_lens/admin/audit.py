"""The console's audit log: who did what, in which role, to what, and how it ended.

A request is written and committed before the change it asks for, and its
outcome after, under one `action_id`. A change can therefore never exist
without a row saying who asked for it; a request with no outcome was cut off
and is shown as such. Nothing that is a key or a secret is ever written here.
"""

import json
import uuid
from contextlib import contextmanager

from sqlalchemy import text

from .. import logs, store

SECRET_WORDS = ("secret", "token", "password", "hash")


def is_secret(name):
    name = name.lower()
    return (
        name == "key"
        or name.endswith("_key")
        or any(word in name for word in SECRET_WORDS)
    )


def scrub(value):
    """The value with anything named like a key or a secret left out."""
    if isinstance(value, dict):
        return {
            name: scrub(item) for name, item in value.items() if not is_secret(name)
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def write(principal, action, target, request, phase, result=None, action_id=None):
    action_id = action_id or str(uuid.uuid4())
    with store.engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO ops.admin_action "
                "(action_id, phase, actor, role, action, target, request, result) "
                "VALUES (:id, :phase, :actor, :role, :action, :target, "
                "CAST(:request AS jsonb), CAST(:result AS jsonb))"
            ),
            {
                "id": action_id,
                "phase": phase,
                "actor": principal.name,
                "role": principal.role,
                "action": action,
                "target": str(target),
                "request": json.dumps(scrub(request or {}), default=str),
                "result": None
                if result is None
                else json.dumps(scrub(result), default=str),
            },
        )
    logs.event(
        "console.action",
        action_id=action_id,
        phase=phase,
        actor=principal.name,
        role=principal.role,
        action=action,
        target=str(target),
    )
    return action_id


def refused(principal, action, target, reason):
    """A request that was turned away: a role that may not, or a budget that would be exceeded."""
    return write(principal, action, target, {}, "refused", {"reason": reason})


@contextmanager
def acting(principal, action, target, request=None):
    """Record a change around the code that makes it.

    Yields a dict the caller fills with a short summary of what happened; it
    becomes the outcome row. An exception is recorded as a failure and raised.
    """
    action_id = write(principal, action, target, request, "requested")
    outcome = {}
    try:
        yield outcome
    except Exception as error:
        write(
            principal,
            action,
            target,
            {},
            "failed",
            {"error_type": type(error).__name__, "error": str(error)[:400]},
            action_id,
        )
        raise
    write(principal, action, target, {}, "done", outcome, action_id)


def listing(limit=200, before=None):
    """Actions, newest first, each with its request and how it ended."""
    query = text(
        "SELECT r.id, r.action_id::text, r.actor, r.role, r.action, r.target, r.request, r.at, "
        "coalesce(o.phase, CASE r.phase WHEN 'refused' THEN 'refused' ELSE 'unfinished' END) AS outcome, "
        "coalesce(o.result, r.result) AS result, o.at AS finished_at "
        "FROM ops.admin_action r "
        "LEFT JOIN ops.admin_action o ON o.action_id = r.action_id AND o.phase IN ('done', 'failed') "
        "WHERE r.phase IN ('requested', 'refused') "
        "AND (CAST(:before AS bigint) IS NULL OR r.id < :before) "
        "ORDER BY r.id DESC LIMIT :limit"
    )
    with store.engine().connect() as connection:
        return [
            {
                **row,
                "at": row["at"].isoformat(),
                "finished_at": row["finished_at"] and row["finished_at"].isoformat(),
            }
            for row in connection.execute(
                query, {"limit": limit, "before": before}
            ).mappings()
        ]
