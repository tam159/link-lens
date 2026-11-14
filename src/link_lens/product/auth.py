"""The auth step: a bearer credential becomes a principal with a tier.

`RESOLVERS` is the seam for a second kind of credential. A resolver takes the
connection and the bearer token and returns a principal or None; adding OAuth
tokens means appending a resolver here, with no change to any interface.
"""

from dataclasses import dataclass

from sqlalchemy import text

from . import Problem, keys

KEY = """
    SELECT key.id AS key_id, key.prefix, sha256_hex(key.key_hash) AS key_hash,
           client.id AS client_id, client.name AS client_name, tier.*
    FROM access.api_key AS key
    JOIN access.client AS client ON client.id = key.client_id
    JOIN access.tier AS tier ON tier.id = client.tier_id
    WHERE key.prefix = :prefix
      AND key.revoked_at IS NULL
      AND (key.expires_at IS NULL OR key.expires_at > now())
      AND client.status = 'active'
"""


@dataclass(frozen=True)
class Principal:
    """Who is calling and what their tier allows."""

    client_id: str
    client_name: str
    key_id: str
    key_prefix: str
    tier: str
    interfaces: frozenset
    toolsets: frozenset
    sources: frozenset | None  # None: every source
    bundle_downloads: bool
    release_lag: int
    history_depth: int | None  # None: every release
    rate_per_minute: int
    monthly_quota: int | None  # None: no monthly limit


def api_key(connection, token):
    """Resolve an API key. Revoked, expired and suspended all look the same: no."""
    parsed = keys.parse(token)
    if parsed is None:
        return None
    prefix, secret = parsed
    row = connection.execute(text(KEY), {"prefix": prefix}).mappings().first()
    if row is None or not keys.matches(secret, row["key_hash"]):
        return None
    return Principal(
        client_id=str(row["client_id"]),
        client_name=row["client_name"],
        key_id=str(row["key_id"]),
        key_prefix=row["prefix"],
        tier=row["id"],
        interfaces=frozenset(row["interfaces"]),
        toolsets=frozenset(row["toolsets"]),
        sources=None if row["source_scope"] is None else frozenset(row["source_scope"]),
        bundle_downloads=row["bundle_downloads"],
        release_lag=row["release_lag"],
        history_depth=row["history_depth"],
        rate_per_minute=row["rate_per_minute"],
        monthly_quota=row["monthly_quota"],
    )


RESOLVERS = [api_key]


def authenticate(connection, authorization, interface):
    """The principal for an `Authorization` header, allowed on `interface`."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Problem(401, "Missing credentials", "Send Authorization: Bearer <key>.")
    for resolve in RESOLVERS:
        principal = resolve(connection, token.strip())
        if principal is not None:
            break
    else:
        raise Problem(
            401, "Invalid credentials", "The key is unknown, expired or revoked."
        )
    if interface not in principal.interfaces:
        raise Problem(
            403, "Interface not in tier", f"This tier does not include {interface}."
        )
    return principal
