"""Limits per key: a rate per minute and a quota per month.

The rate limit is a token bucket. `DatabaseLimiter` keeps each key's bucket in
PostgreSQL, so every instance of the service draws on the same one;
`RateLimiter` keeps it in memory, which is correct for one instance. Usage is
counted per key, day and interface; the monthly quota is the client's total
across its keys.
"""

import math
import threading
import time
from datetime import UTC, datetime

from sqlalchemy import text

from ..settings import settings
from . import Problem


class RateLimiter:
    """A token bucket per key in this process: `per_minute` tokens, refilled evenly."""

    def __init__(self, clock=time.monotonic):
        self.clock, self.buckets, self.lock = clock, {}, threading.Lock()

    def take(self, connection, key, per_minute):
        """Take one token. Returns None, or the seconds until one is available."""
        now = self.clock()
        with self.lock:
            tokens, updated = self.buckets.get(key, (float(per_minute), now))
            tokens = min(float(per_minute), tokens + (now - updated) * per_minute / 60)
            if tokens < 1:
                self.buckets[key] = (tokens, now)
                return (1 - tokens) * 60 / per_minute
            self.buckets[key] = (tokens - 1, now)
            return None


# Tokens the bucket holds now: what it held, refilled for the time since.
REFILLED = (
    "LEAST(:rate, bucket.tokens + GREATEST(extract(epoch FROM "
    "(COALESCE(CAST(:at AS timestamptz), clock_timestamp()) - bucket.updated_at)), 0) "
    "* :rate / 60.0)"
)
TAKE = f"""
    INSERT INTO access.rate_bucket AS bucket (key_id, tokens, updated_at)
    VALUES (CAST(:key AS uuid), :rate - 1,
            COALESCE(CAST(:at AS timestamptz), clock_timestamp()))
    ON CONFLICT (key_id) DO UPDATE
    SET tokens = {REFILLED} - 1,
        updated_at = COALESCE(CAST(:at AS timestamptz), clock_timestamp())
    WHERE {REFILLED} >= 1
    RETURNING tokens
"""
WAIT = f"""
    SELECT (1 - {REFILLED}) * 60.0 / :rate
    FROM access.rate_bucket AS bucket WHERE key_id = CAST(:key AS uuid)
"""


class DatabaseLimiter:
    """A token bucket per key in PostgreSQL, shared by every instance.

    One statement refills and takes, so two instances cannot both take the last
    token. Time is the database's own unless a clock is given, as tests do.
    """

    def __init__(self, clock=None):
        self.clock = clock

    def take(self, connection, key, per_minute):
        at = None
        if self.clock is not None:
            at = datetime.fromtimestamp(self.clock(), UTC)
        parameters = {"key": key, "rate": float(per_minute), "at": at}
        if connection.execute(text(TAKE), parameters).first() is not None:
            return None
        return float(connection.execute(text(WAIT), parameters).scalar_one())


# Set to a limiter to override the configured one, as tests do.
limiter = None
_configured = {}


def configured():
    kind = settings().rate_limit_store
    if kind not in _configured:
        _configured[kind] = DatabaseLimiter() if kind == "database" else RateLimiter()
    return _configured[kind]


def seconds_to_next_month(now):
    following = (
        now.replace(year=now.year + 1, month=1)
        if now.month == 12
        else now.replace(month=now.month + 1)
    )
    start = following.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return math.ceil((start - now).total_seconds())


def enforce(connection, principal, interface, now=None):
    """Refuse a call that is over a limit; otherwise count it."""
    wait = (limiter or configured()).take(
        connection, principal.key_id, principal.rate_per_minute
    )
    if wait is not None:
        raise Problem(
            429,
            "Rate limit reached",
            f"This tier allows {principal.rate_per_minute} calls a minute.",
            retry_after=math.ceil(wait),
        )
    now = now or datetime.now(UTC)
    if principal.monthly_quota is not None:
        used = connection.execute(
            text(
                "SELECT coalesce(sum(usage.calls), 0) FROM access.api_usage AS usage "
                "JOIN access.api_key AS key ON key.id = usage.key_id "
                "WHERE key.client_id = :client AND usage.day >= :month"
            ),
            {"client": principal.client_id, "month": now.date().replace(day=1)},
        ).scalar_one()
        if used >= principal.monthly_quota:
            raise Problem(
                429,
                "Monthly quota reached",
                f"This tier allows {principal.monthly_quota} calls a month.",
                retry_after=seconds_to_next_month(now),
            )
    connection.execute(
        text(
            "INSERT INTO access.api_usage (key_id, day, interface, calls) "
            "VALUES (:key, :day, :interface, 1) "
            "ON CONFLICT (key_id, day, interface) "
            "DO UPDATE SET calls = access.api_usage.calls + 1"
        ),
        {"key": principal.key_id, "day": now.date(), "interface": interface},
    )
