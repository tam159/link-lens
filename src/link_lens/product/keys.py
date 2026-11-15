"""Tiers, clients and API keys. Administration runs as the pipeline, not the product role.

A key is `ll_<prefix>_<secret>`. The prefix finds the key's row; the row holds
the SHA-256 of the secret, never the secret. The full key is returned once, when
it is created, and is never logged.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from .. import store

INTERFACES = ("rest", "mcp", "graphql")
TOOLSETS = ("data", "files")


def digest(secret):
    return hashlib.sha256(secret.encode()).hexdigest()


def parse(token):
    """The prefix and secret of a key, or None when it is not shaped like one."""
    parts = token.split("_") if isinstance(token, str) else []
    if len(parts) != 3 or parts[0] != "ll" or not parts[1] or len(parts[2]) < 64:
        return None
    return parts[1], parts[2]


def matches(secret, key_hash):
    """Compare in constant time, so timing reveals nothing about the hash."""
    return hmac.compare_digest(digest(secret), key_hash)


def set_tier(
    tier_id,
    rate_per_minute,
    monthly_quota=None,
    interfaces=("rest",),
    toolsets=(),
    source_scope=None,
    bundle_downloads=False,
    release_lag=0,
    history_depth=None,
):
    """Create a tier or replace its limits. Clients on the tier follow at once."""
    unknown = set(interfaces) - set(INTERFACES) or set(toolsets) - set(TOOLSETS)
    if unknown:
        raise ValueError(f"Unknown interface or toolset: {sorted(unknown)}")
    values = {
        "id": tier_id,
        "rate": rate_per_minute,
        "quota": monthly_quota,
        "interfaces": list(interfaces),
        "toolsets": list(toolsets),
        "scope": None if source_scope is None else list(source_scope),
        "bundles": bundle_downloads,
        "lag": release_lag,
        "depth": history_depth,
    }
    with store.engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO access.tier (id, rate_per_minute, monthly_quota, interfaces,
                    toolsets, source_scope, bundle_downloads, release_lag, history_depth)
                VALUES (:id, :rate, :quota, :interfaces, :toolsets, :scope, :bundles,
                    :lag, :depth)
                ON CONFLICT (id) DO UPDATE SET
                    rate_per_minute = excluded.rate_per_minute,
                    monthly_quota = excluded.monthly_quota,
                    interfaces = excluded.interfaces,
                    toolsets = excluded.toolsets,
                    source_scope = excluded.source_scope,
                    bundle_downloads = excluded.bundle_downloads,
                    release_lag = excluded.release_lag,
                    history_depth = excluded.history_depth
                """
            ),
            values,
        )
    return tier(tier_id)


def tier(tier_id):
    with store.engine().connect() as connection:
        row = (
            connection.execute(
                text("SELECT * FROM access.tier WHERE id = :id"), {"id": tier_id}
            )
            .mappings()
            .first()
        )
    if row is None:
        raise KeyError(f"tiers/{tier_id} not found")
    return dict(row)


def create_client(name, tier_id):
    tier(tier_id)
    client_id = uuid.uuid4()
    with store.engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO access.client (id, name, tier_id) VALUES (:id, :name, :tier)"
            ),
            {"id": client_id, "name": name, "tier": tier_id},
        )
    return {
        "client_id": str(client_id),
        "name": name,
        "tier_id": tier_id,
        "status": "active",
    }


def set_client_status(client_id, status):
    with store.engine().begin() as connection:
        changed = connection.execute(
            text("UPDATE access.client SET status = :status WHERE id = :id"),
            {"id": client_id, "status": status},
        ).rowcount
    if not changed:
        raise KeyError(f"clients/{client_id} not found")
    return {"client_id": str(client_id), "status": status}


def create_key(client_id, label=None, expires_in_days=None):
    """Create a key for a client. The returned `key` is shown this once only."""
    prefix, secret = secrets.token_hex(6), secrets.token_hex(32)
    key_id = uuid.uuid4()
    expires = (
        None
        if expires_in_days is None
        else datetime.now(UTC) + timedelta(days=expires_in_days)
    )
    with store.engine().begin() as connection:
        if not connection.execute(
            text("SELECT 1 FROM access.client WHERE id = :id"), {"id": client_id}
        ).first():
            raise KeyError(f"clients/{client_id} not found")
        connection.execute(
            text(
                "INSERT INTO access.api_key (id, client_id, prefix, key_hash, label, expires_at) "
                "VALUES (:id, :client, :prefix, sha256_from_hex(:hash), :label, :expires)"
            ),
            {
                "id": key_id,
                "client": client_id,
                "prefix": prefix,
                "hash": digest(secret),
                "label": label,
                "expires": expires,
            },
        )
    return {
        "key_id": str(key_id),
        "client_id": str(client_id),
        "prefix": prefix,
        "label": label,
        "expires_at": expires.isoformat() if expires else None,
        "key": f"ll_{prefix}_{secret}",
    }


def revoke_key(prefix):
    """Revoke a key by its prefix. Revoking twice keeps the first time."""
    with store.engine().begin() as connection:
        row = connection.execute(
            text(
                "UPDATE access.api_key SET revoked_at = coalesce(revoked_at, now()) "
                "WHERE prefix = :prefix RETURNING id, revoked_at"
            ),
            {"prefix": prefix},
        ).first()
    if row is None:
        raise KeyError(f"keys/{prefix} not found")
    return {
        "key_id": str(row.id),
        "prefix": prefix,
        "revoked_at": row.revoked_at.isoformat(),
    }


def usage(client_id=None, since=None):
    """Calls per client, key, interface and month."""
    with store.engine().connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT client.id AS client_id, client.name AS client, client.tier_id,
                       key.prefix, usage.interface,
                       to_char(date_trunc('month', usage.day), 'YYYY-MM') AS month,
                       sum(usage.calls)::bigint AS calls
                FROM access.api_usage AS usage
                JOIN access.api_key AS key ON key.id = usage.key_id
                JOIN access.client AS client ON client.id = key.client_id
                WHERE (CAST(:client AS uuid) IS NULL OR client.id = :client)
                  AND (CAST(:since AS date) IS NULL OR usage.day >= :since)
                GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY 2, 6, 4, 5
                """
            ),
            {"client": client_id, "since": since},
        ).mappings()
        return [{**row, "client_id": str(row["client_id"])} for row in rows]
