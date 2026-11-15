"""Repository for the `catalog` schema: artifacts, sources and snapshots."""

from sqlalchemy import (
    BigInteger,
    Integer,
    Column,
    DateTime,
    Interval,
    MetaData,
    Table,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert

from .records import Field, RecordTable, parse_time
from .types import Sha256

metadata = MetaData(schema="catalog")
timestamp = DateTime(timezone=True)

artifact = Table(
    "artifact",
    metadata,
    Column("sha256", Sha256, primary_key=True),
    Column("uri", Text),
    Column("media_type", Text),
    Column("size", BigInteger),
    Column("name", Text),
    Column("created_at", timestamp),
)
source = Table(
    "source",
    metadata,
    Column("id", Text, primary_key=True),
    Column("owner_id", Text),
    Column("kind", Text),
    Column("portal", Text),
    Column("slug", Text),
    Column("metadata", JSONB(none_as_null=True)),
    Column("extra", JSONB),
    Column("created_at", timestamp),
)
snapshot = Table(
    "snapshot",
    metadata,
    Column("id", Text, primary_key=True),
    Column("owner_id", Text),
    Column("kind", Text),
    Column("source_id", Text),
    Column("resource_id", Text),
    Column("artifact_sha", Sha256),
    Column("format", Text),
    Column("licence", Text),
    Column("licence_url", Text),
    Column("observed_at", timestamp),
    Column("observed_at_basis", Text),
    Column("retrieved_at", timestamp),
    Column("documentation", JSONB(none_as_null=True)),
    Column("dataset_notes", Text),
    Column("receipt", JSONB(none_as_null=True)),
    Column("inspection", JSONB(none_as_null=True)),
    Column("extra", JSONB),
    Column("created_at", timestamp),
)


source_refresh = Table(
    "source_refresh",
    metadata,
    Column("source_id", Text, primary_key=True),
    Column("cadence", Interval),
    Column("last_checked_at", timestamp),
    Column("updated_at", timestamp),
    Column("paused_at", timestamp),
    Column("paused_by", Text),
    Column("consecutive_failures", Integer),
    Column("last_failure_at", timestamp),
    Column("last_error", Text),
)


class SnapshotTable(RecordTable):
    def split(self, connection, payload):
        columns = super().split(connection, payload)
        receipt = payload.get("receipt")
        # A projection of the receipt for queries; the receipt stays the record.
        columns["retrieved_at"] = parse_time(
            receipt.get("retrieved_at") if isinstance(receipt, dict) else None
        )
        return columns


sources = RecordTable(
    "sources",
    source,
    [
        Field("portal", "portal", "text"),
        Field("slug", "slug", "text"),
        Field("metadata", "metadata", "json"),
    ],
)
snapshots = SnapshotTable(
    "snapshots",
    snapshot,
    [
        Field("source_id", "source_id", "text", references=source.c.id),
        Field("resource_id", "resource_id", "text"),
        Field("artifact_id", "artifact_sha", "sha256", references=artifact.c.sha256),
        Field("format", "format", "text"),
        Field("licence", "licence", "text"),
        Field("licence_url", "licence_url", "text"),
        Field("observed_at", "observed_at", "timestamp"),
        Field("observed_at_basis", "observed_at_basis", "text"),
        Field("documentation", "documentation", "json"),
        Field("dataset_notes", "dataset_notes", "text"),
        Field("receipt", "receipt", "json"),
        Field("inspection", "inspection", "json"),
    ],
    append_only=True,
)


def artifact_record(row):
    """An artifact as the store has always described it."""
    return {
        "id": row.sha256,
        "sha256": row.sha256,
        "size": row.size,
        "media_type": row.media_type,
        "name": row.name,
    }


def get_artifact(connection, key):
    row = connection.execute(select(artifact).where(artifact.c.sha256 == key)).first()
    return None if row is None else artifact_record(row)


def artifact_uri(connection, key):
    return connection.execute(
        select(artifact.c.uri).where(artifact.c.sha256 == key)
    ).scalar_one_or_none()


def put_artifact(connection, record, uri, created_at=None):
    """Register an artifact. Content is the identity, so an existing row is kept."""
    if (
        set(record) != {"id", "sha256", "size", "media_type", "name"}
        or record["id"] != record["sha256"]
    ):
        raise ValueError("An artifact record holds id, sha256, size, media_type, name")
    values = {
        "sha256": record["sha256"],
        "uri": uri,
        "media_type": record["media_type"],
        "size": record["size"],
        "name": record["name"],
    }
    if created_at is not None:
        values["created_at"] = created_at
    connection.execute(insert(artifact).values(values).on_conflict_do_nothing())


def artifact_records(connection):
    for row in connection.execute(
        select(artifact).order_by(artifact.c.created_at, artifact.c.sha256)
    ):
        yield row.sha256, "", "", artifact_record(row), row.created_at
