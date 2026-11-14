"""Limits per key: a rate per minute in this process, a quota per month in the database.

The rate limit is a token bucket held in memory, which is correct for one
instance of the service. Usage is counted per key, day and interface; the
monthly quota is the client's total across its keys.
"""

import math
import threading
import time
from datetime import UTC, datetime

from sqlalchemy import text

from . import Problem


class RateLimiter:
    """A token bucket per key: `per_minute` tokens, refilled evenly."""

    def __init__(self, clock=time.monotonic):
        self.clock, self.buckets, self.lock = clock, {}, threading.Lock()

    def take(self, key, per_minute):
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


limiter = RateLimiter()


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
    wait = limiter.take(principal.key_id, principal.rate_per_minute)
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
