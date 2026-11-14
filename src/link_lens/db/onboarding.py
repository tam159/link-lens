"""Repository for the `onboarding` schema: runs, mapping configs, mappings, approvals."""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert

from . import catalog
from . import ontology as registry
from .records import Field, RecordTable, same
from .types import Sha256, is_sha256

metadata = MetaData(schema="onboarding")
timestamp = DateTime(timezone=True)

run = Table(
    "run",
    metadata,
    Column("id", Text, primary_key=True),
    Column("owner_id", Text),
    Column("kind", Text),
    Column("experiment_id", Text),
    Column("source_id", Text),
    Column("snapshot_id", Text),
    Column("ontology_hash", Sha256),
    Column("supersedes_run_id", Text),
    Column("status", Text),
    Column("model", Text),
    Column("prompt_version", Text),
    Column("thread_id", Text),
    Column("model_calls", Integer),
    Column("python_calls", Integer),
    Column("input_tokens", BigInteger),
    Column("output_tokens", BigInteger),
    Column("active_seconds", Float),
    Column("calculated_cost_usd", Float),
    Column("started_at", timestamp),
    Column("completed_at", timestamp),
    Column("state", JSONB),
    Column("created_at", timestamp),
)
mapping_config = Table(
    "mapping_config",
    metadata,
    Column("config_hash", Sha256, primary_key=True),
    Column("config", JSONB),
    Column("ontology_hash", Sha256),
    Column("subject_role", Text),
    Column("source_kind", Text),
    Column("address_role", Text),
    Column("source_reliability", Float),
    Column("created_at", timestamp),
)
mapping_field = Table(
    "mapping_field",
    metadata,
    Column("config_hash", Sha256, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("concept_id", BigInteger),
    Column("group_name", Text),
    Column("source_fields", ARRAY(Text)),
)
mapping = Table(
    "mapping",
    metadata,
    Column("id", Text, primary_key=True),
    Column("owner_id", Text),
    Column("kind", Text),
    Column("run_id", Text),
    Column("version", Integer),
    Column("config_hash", Sha256),
    Column("model", Text),
    Column("status", Text),
    Column("generated_by", Text),
    Column("proposed_at", timestamp),
    Column("extra", JSONB),
    Column("created_at", timestamp),
)
approval = Table(
    "approval",
    metadata,
    Column("id", Text, primary_key=True),
    Column("owner_id", Text),
    Column("kind", Text),
    Column("run_id", Text),
    Column("mapping_id", Text),
    Column("config_hash", Sha256),
    Column("decision", Text),
    Column("reviewer", Text),
    Column("feedback", Text),
    Column("identity_basis", Text),
    Column("decided_at", timestamp),
    Column("extra", JSONB),
    Column("created_at", timestamp),
)


def ensure_config(connection, config_hash, config, content_hash, root_hash):
    """Store a mapping config under its content hash. False if it cannot be.

    A config is stored only when it hashes to `config_hash`, names its roles and
    reliability, and its ontology version is registered. Its fields are indexed
    by concept for impact queries. `root_hash` is the packaged ontology that
    configs without an `ontology_hash` use.
    """
    if not is_sha256(config_hash) or not isinstance(config, dict):
        return False
    stored = connection.execute(
        select(mapping_config.c.config).where(
            mapping_config.c.config_hash == config_hash
        )
    ).first()
    if stored is not None:
        return same(stored.config, config)
    reliability = config.get("source_reliability")
    version = config.get("ontology_hash") or root_hash
    if (
        content_hash(config) != config_hash
        or not all(
            isinstance(config.get(key), str)
            for key in ("subject_role", "source_kind", "address_role")
        )
        or isinstance(reliability, bool)
        or not isinstance(reliability, (int, float))
        or not is_sha256(version)
        or registry.version(connection, version) is None
    ):
        return False
    connection.execute(
        insert(mapping_config)
        .values(
            config_hash=config_hash,
            config=config,
            ontology_hash=config.get("ontology_hash"),
            subject_role=config["subject_role"],
            source_kind=config["source_kind"],
            address_role=config["address_role"],
            source_reliability=float(reliability),
        )
        .on_conflict_do_nothing()
    )
    concepts = registry.concept_ids(connection, version)
    rows = [
        {
            "config_hash": config_hash,
            "position": position,
            "concept_id": concepts[field["canonical_field"]],
            "group_name": field.get("group") or "",
            "source_fields": field.get("source_fields") or [],
        }
        for position, field in enumerate(config.get("fields") or [])
        if isinstance(field, dict) and field.get("canonical_field") in concepts
    ]
    if rows:
        connection.execute(insert(mapping_field).on_conflict_do_nothing(), rows)
    return True


class MappingTable(RecordTable):
    """A mapping's config lives in `mapping_config`; the mapping references it."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_hash = self.root_hash = None

    def statement(self):
        return select(self.table, mapping_config.c.config).join(
            mapping_config,
            mapping_config.c.config_hash == self.table.c.config_hash,
            isouter=True,
        )

    def split(self, connection, payload):
        stored = "config" in payload and ensure_config(
            connection,
            payload.get("config_hash"),
            payload["config"],
            self.content_hash,
            self.root_hash,
        )
        rest = {
            k: v
            for k, v in payload.items()
            if not (stored and k in ("config", "config_hash"))
        }
        columns = super().split(connection, rest)
        columns["config_hash"] = payload["config_hash"] if stored else None
        return columns

    def join(self, row):
        payload = super().join(row)
        if row["config_hash"] is not None:
            payload["config_hash"] = row["config_hash"]
            payload["config"] = row["config"]
        return payload


runs = RecordTable(
    "runs",
    run,
    [
        Field("experiment_id", "experiment_id", "text"),
        Field("source_id", "source_id", "text", references=catalog.source.c.id),
        Field("snapshot_id", "snapshot_id", "text", references=catalog.snapshot.c.id),
        Field(
            "ontology_hash",
            "ontology_hash",
            "sha256",
            references=registry.ontology_version.c.hash,
        ),
        Field("supersedes_run_id", "supersedes_run_id", "text", references=run.c.id),
        Field("status", "status", "text"),
        Field("model", "model", "text"),
        Field("prompt_version", "prompt_version", "text"),
        Field("thread_id", "thread_id", "text"),
        Field("model_calls", "model_calls", "integer"),
        Field("python_calls", "python_calls", "integer"),
        Field("input_tokens", "input_tokens", "integer"),
        Field("output_tokens", "output_tokens", "integer"),
        Field("active_seconds", "active_seconds", "float"),
        Field("calculated_cost_usd", "calculated_cost_usd", "float"),
        Field("created_at", "started_at", "timestamp"),
        Field("completed_at", "completed_at", "timestamp"),
    ],
    extra="state",
)
mappings = MappingTable(
    "mappings",
    mapping,
    [
        Field("run_id", "run_id", "text", references=run.c.id),
        Field("version", "version", "integer"),
        Field("model", "model", "text"),
        Field("status", "status", "text"),
        Field("generated_by", "generated_by", "text"),
        Field("created_at", "proposed_at", "timestamp"),
    ],
    append_only=True,
)
approvals = RecordTable(
    "approvals",
    approval,
    [
        Field("run_id", "run_id", "text", references=run.c.id),
        Field("mapping_id", "mapping_id", "text", references=mapping.c.id),
        Field(
            "config_hash",
            "config_hash",
            "sha256",
            references=mapping_config.c.config_hash,
        ),
        Field("decision", "decision", "text"),
        Field("reviewer", "reviewer", "text"),
        Field("feedback", "feedback", "text"),
        Field("identity_basis", "identity_basis", "text"),
        Field("at", "decided_at", "timestamp"),
    ],
    append_only=True,
)
