"""PostgreSQL is authoritative; blobs are immutable and addressed by SHA-256."""

import hashlib
import json
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .settings import settings

metadata = MetaData()
# Each domain has a distinct table and indexed ownership keys. Payloads are validated
# by domain contracts; keeping complete evidence as JSON avoids lossy flattening.
TABLES = {}
for name in [
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
        Column("payload", JSON, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )


def now():
    return datetime.now(UTC).isoformat()


@lru_cache
def engine():
    return create_engine(settings().database_url, pool_pre_ping=True)


def put(table, key, payload, owner="", kind="", *, immutable=False):
    t = TABLES[table]
    if immutable:
        old = get(table, key)
        if old is not None and old != payload:
            raise ValueError(f"Immutable {table}/{key} already exists")
    factory = sqlite_insert if engine().dialect.name == "sqlite" else pg_insert
    query = factory(t).values(
        id=key,
        owner_id=owner,
        kind=kind,
        payload=payload,
        created_at=datetime.now(UTC),
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


def get(table, key):
    with engine().connect() as connection:
        return connection.execute(
            select(TABLES[table].c.payload).where(TABLES[table].c.id == key)
        ).scalar_one_or_none()


def require(table, key):
    value = get(table, key)
    if value is None:
        raise KeyError(f"{table}/{key} not found")
    return value


def listing(table, owner=None, kind=None):
    t = TABLES[table]
    query = select(t.c.payload).order_by(t.c.created_at, t.c.id)
    if owner is not None:
        query = query.where(t.c.owner_id == owner)
    if kind is not None:
        query = query.where(t.c.kind == kind)
    with engine().connect() as connection:
        return list(connection.execute(query).scalars())


def blob(data: bytes, media_type="application/json", name="artifact"):
    sha = hashlib.sha256(data).hexdigest()
    path = settings().artifact_dir / "blobs" / sha[:2] / sha
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temp = path.with_suffix(".tmp")
        temp.write_bytes(data)
        temp.replace(path)
    record = {
        "id": sha,
        "sha256": sha,
        "size": len(data),
        "media_type": media_type,
        "name": name,
    }
    # Content deduplication may reuse an earlier display name; content is the identity.
    if get("artifacts", sha) is None:
        put("artifacts", sha, record, immutable=True)
    return sha


def blob_path(key):
    require("artifacts", key)
    if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise ValueError("Invalid artifact ID")
    path = settings().artifact_dir / "blobs" / key[:2] / key
    if not path.is_file():
        raise FileNotFoundError(key)
    return path


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


from contextlib import contextmanager
from threading import Lock

_local_model_lock = Lock()


@contextmanager
def model_budget_lock():
    """Serialize reservations across local backend workers, including smoke calls."""
    if engine().dialect.name == "postgresql":
        from sqlalchemy import text

        with (
            engine()
            .connect()
            .execution_options(isolation_level="AUTOCOMMIT") as connection
        ):
            connection.execute(
                text("SELECT pg_advisory_lock(hashtext('link-lens-model-budget'))")
            )
            try:
                yield
            finally:
                connection.execute(
                    text(
                        "SELECT pg_advisory_unlock(hashtext('link-lens-model-budget'))"
                    )
                )
    else:
        with _local_model_lock:
            yield


def current_discovery(experiment_id=None):
    """Resolve the active revision without rewriting historical discovery evidence."""
    if experiment_id:
        return get("batches", "discovery-current-" + experiment_id) or get(
            "batches", "discovery-" + experiment_id
        )
    return get("batches", "discovery")
