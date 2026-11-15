"""PostgreSQL is authoritative; blobs are immutable and addressed by SHA-256.

This module is the store facade: callers read and write one JSON record per key
in a named table. Tables whose domain has moved to typed schemas are served from
those schemas and return the same records; the rest are still the generic tables
in `legacy`.
"""

import hashlib
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

from . import blobs
from .db import catalog, evidence, identity, is_sha256, onboarding, ops
from .settings import settings

metadata = MetaData()
# Each domain has a distinct table and indexed ownership keys. Payloads are validated
# by domain contracts; keeping complete evidence as JSON avoids lossy flattening.
# These generic tables live in the `legacy` schema while each domain moves to typed
# tables. Alembic migrations own the DDL; this metadata is only used to build queries.
TABLES = {}
for name in [
    "ontologies",
    "ontology_events",
    "budget_reservations",
    "sources",
    "snapshots",
    "runs",
    "mappings",
    "approvals",
    "observations",
    "entities",
    "memberships",
    "links",
    "profiles",
    "evaluations",
    "artifacts",
    "events",
    "batches",
]:
    TABLES[name] = Table(
        name,
        metadata,
        Column("id", String(128), primary_key=True),
        Column("owner_id", String(128), nullable=False, index=True),
        Column("kind", String(80), nullable=False, index=True),
        Column("payload", JSONB, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        schema="legacy",
    )


def now():
    return datetime.now(UTC).isoformat()


@lru_cache
def engine():
    role = settings().database_role
    if role and not role.replace("_", "").isalnum():
        raise ValueError(f"Not a role name: {role}")
    # The role is set when a connection opens, so every statement of the process
    # has that role's rights and no more.
    options = {"connect_args": {"options": f"-c role={role}"}} if role else {}
    return create_engine(settings().database_url, pool_pre_ping=True, **options)


# Tables served from typed schemas. Each keeps the record it was given exactly.
RECORDS = {
    "sources": catalog.sources,
    "snapshots": catalog.snapshots,
    "runs": onboarding.runs,
    "mappings": onboarding.mappings,
    "approvals": onboarding.approvals,
    "entities": identity.entities,
    "memberships": identity.memberships,
    "links": identity.links,
    "profiles": identity.profiles,
    "evaluations": ops.evaluations,
    "events": ops.events,
    "budget_reservations": ops.model_calls,
}
TYPED = ("artifacts", *RECORDS, "observations", "batches")
# Legacy rows that are history only: ontology versions and the events that
# proposed and activated them now live in the ontology registry.
HISTORY = ("ontologies", "ontology_events")


def record_table(table, key, kind=None):
    """The typed table that holds a record, or None while it is still generic."""
    if table in RECORDS:
        return RECORDS[table]
    if table == "batches":
        return ops.batch_table(key, kind)
    if table == "ontology_events" and (
        kind == "model_cache" or key.startswith("call-")
    ):
        return ops.model_caches
    return None


def _root_hash():
    """The packaged ontology, which mappings without an ontology_hash use."""
    from . import ontology

    return ontology.digest(ontology.legacy())


def _prepare_mappings():
    from . import ontology
    from .contracts import content_hash

    # Mapping fields are indexed by concept, so the packaged ontology must be
    # registered before a mapping that relies on it is stored.
    ontology.register(ontology.legacy())
    onboarding.mappings.content_hash = content_hash
    onboarding.mappings.root_hash = _root_hash()


def put(table, key, payload, owner="", kind="", *, immutable=False, created_at=None):
    if table == "observations":
        if payload.get("id") != key:
            raise ValueError("An observation is stored under its own id")
        put_observations([payload])
        return payload
    if table == "artifacts":
        with engine().begin() as connection:
            uri = catalog.artifact_uri(connection, key) or "local:" + blobs.relative(
                key
            )
            catalog.put_artifact(connection, payload, uri, created_at)
        return payload
    target = record_table(table, key, kind)
    if target is not None:
        if table == "mappings":
            _prepare_mappings()
        with engine().begin() as connection:
            target.put(connection, key, payload, owner, kind, immutable, created_at)
        return payload
    t = TABLES[table]
    if immutable:
        old = get(table, key)
        if old is not None and old != payload:
            raise ValueError(f"Immutable {table}/{key} already exists")
    query = pg_insert(t).values(
        id=key,
        owner_id=owner,
        kind=kind,
        payload=payload,
        created_at=created_at or datetime.now(UTC),
    )
    query = (
        query.on_conflict_do_nothing(index_elements=["id"])
        if immutable
        else query.on_conflict_do_update(
            index_elements=["id"],
            set_={"payload": payload, "owner_id": owner, "kind": kind},
        )
    )
    with engine().begin() as connection:
        connection.execute(query)
    return payload


def put_many(records):
    """Write several records in one transaction, in the order given.

    Each record is `(table, key, payload, owner, kind, immutable)`. A batch is
    written this way: the batch row first, then everything it owns, so the batch
    and its entities, memberships, links and profiles appear together or not at
    all.
    """
    records = list(records)
    if any(table == "mappings" for table, *_ in records):
        _prepare_mappings()
    with engine().begin() as connection:
        for table, key, payload, owner, kind, immutable in records:
            target = record_table(table, key, kind)
            if target is None:
                raise ValueError(f"{table} cannot be written with put_many")
            target.put(connection, key, payload, owner, kind, immutable)
    return len(records)


def put_embedding(key, model, vector):
    """Keep an embedding for similarity search; a stored one is left unchanged."""
    with engine().begin() as connection:
        return ops.put_embedding(connection, key, model, vector)


def charged(owner, kind):
    """Budget charged so far by one owner's events of a kind."""
    with engine().connect() as connection:
        return ops.charged(connection, owner, kind)


def put_observations(observations):
    """Store observations in bulk. Returns how many were not stored already."""
    from . import ontology

    observations = list(observations)
    if not observations:
        return 0
    ontology.register(ontology.legacy())
    with engine().begin() as connection:
        return evidence.insert_observations(connection, observations, _root_hash())


def get(table, key):
    with engine().connect() as connection:
        if table == "observations":
            found = (
                list(evidence.observations(connection, [key])) if is_sha256(key) else []
            )
            return found[0] if found else None
        if table == "artifacts":
            return catalog.get_artifact(connection, key) if is_sha256(key) else None
        target = record_table(table, key)
        if target is not None:
            found = target.get(connection, key)
            if found is not None or table != "ontology_events":
                return found
        return connection.execute(
            select(TABLES[table].c.payload).where(TABLES[table].c.id == key)
        ).scalar_one_or_none()


def require(table, key):
    value = get(table, key)
    if value is None:
        raise KeyError(f"{table}/{key} not found")
    return value


@contextmanager
def _reading(connection):
    if connection is not None:
        yield connection
    else:
        with engine().connect() as opened:
            yield opened


def records(table, owner=None, kind=None, connection=None):
    """Records of a table as {id, owner_id, kind, payload}, in listing order."""
    with _reading(connection) as connection:
        if table == "observations":
            # An observation belongs to its source record, not to whoever stored
            # it first, so the generic owner is no longer kept.
            if owner is not None:
                raise ValueError("Observations cannot be listed by owner")
            rows = (
                (o["id"], "", "observation", o, None)
                for o in evidence.observations(connection)
                if kind in (None, "observation")
            )
        elif table == "artifacts":
            rows = (
                r
                for r in catalog.artifact_records(connection)
                if owner in (None, "") and kind in (None, "")
            )
        elif table in RECORDS:
            rows = RECORDS[table].records(connection, owner, kind)
        elif table == "batches":
            # Batches, triage decisions and cached responses were one table.
            rows = sorted(
                (
                    row
                    for part in ops.batch_tables(kind)
                    for row in part.records(connection, owner, kind)
                    if row[2] != "model_cache"
                ),
                key=lambda row: (row[4], row[0]),
            )
        else:
            t = TABLES[table]
            query = select(t.c.id, t.c.owner_id, t.c.kind, t.c.payload, t.c.created_at)
            query = query.order_by(t.c.created_at, t.c.id)
            if owner is not None:
                query = query.where(t.c.owner_id == owner)
            if kind is not None:
                query = query.where(t.c.kind == kind)
            rows = list(connection.execute(query))
            if table == "ontology_events":
                # Cached model responses moved to ops; the rest is history.
                rows = sorted(
                    [row for row in rows if row[2] != "model_cache"]
                    + [
                        row
                        for row in ops.model_caches.records(connection, owner, kind)
                        if row[2] == "model_cache"
                    ],
                    key=lambda row: (row[4], row[0]),
                )
        for key, row_owner, row_kind, payload, _ in rows:
            yield {
                "id": key,
                "owner_id": row_owner,
                "kind": row_kind,
                "payload": payload,
            }


def listing(table, owner=None, kind=None):
    return [record["payload"] for record in records(table, owner, kind)]


def blob(data: bytes, media_type="application/json", name="artifact"):
    sha = hashlib.sha256(data).hexdigest()
    with engine().connect() as connection:
        uri = catalog.artifact_uri(connection, sha)
    if uri is None:
        uri = blobs.put(sha, data)
    elif uri.startswith("local:"):
        # Registered locally: make sure the bytes are in this artifact directory.
        blobs.stores()["local"].put(sha, data)
    record = {
        "id": sha,
        "sha256": sha,
        "size": len(data),
        "media_type": media_type,
        "name": name,
    }
    # Content deduplication may reuse an earlier display name; content is the identity.
    with engine().begin() as connection:
        catalog.put_artifact(connection, record, uri)
    return sha


def blob_path(key):
    if not is_sha256(key):
        raise KeyError(f"artifacts/{key} not found")
    with engine().connect() as connection:
        uri = catalog.artifact_uri(connection, key)
    if uri is None:
        raise KeyError(f"artifacts/{key} not found")
    return blobs.path(uri, key)


def json_blob(value, name="artifact.json"):
    return blob(
        json.dumps(value, ensure_ascii=False, indent=2, default=str).encode(), name=name
    )


def read_json(key):
    return json.loads(blob_path(key).read_bytes())


def event(run_id, kind, payload):
    import uuid

    value = {
        "id": str(uuid.uuid4()),
        "run_id": run_id,
        "kind": kind,
        "at": now(),
        **payload,
    }
    put("events", value["id"], value, run_id, kind)
    return value


@contextmanager
def model_budget_lock():
    """Serialize reservations across local backend workers, including smoke calls."""
    from sqlalchemy import text

    with (
        engine().connect().execution_options(isolation_level="AUTOCOMMIT") as connection
    ):
        connection.execute(
            text("SELECT pg_advisory_lock(hashtext('link-lens-model-budget'))")
        )
        try:
            yield
        finally:
            connection.execute(
                text("SELECT pg_advisory_unlock(hashtext('link-lens-model-budget'))")
            )


def current_discovery(experiment_id=None):
    """Resolve the active revision without rewriting historical discovery evidence."""
    if experiment_id:
        return get("batches", "discovery-current-" + experiment_id) or get(
            "batches", "discovery-" + experiment_id
        )
    return get("batches", "discovery")
