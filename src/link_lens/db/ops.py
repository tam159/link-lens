"""Repository for the `ops` schema: batches, triage decisions, model cache,
model calls, events, evaluations and embeddings."""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Column,
    DateTime,
    Float,
    MetaData,
    Table,
    Text,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from . import catalog
from .records import Field, RecordTable
from .types import Sha256

metadata = MetaData(schema="ops")
timestamp = DateTime(timezone=True)
EMBEDDING_DIMENSIONS = 1536


def record_columns():
    return [
        Column("id", Text, primary_key=True),
        Column("owner_id", Text),
        Column("kind", Text),
    ]


def record_tail():
    return [Column("extra", JSONB), Column("created_at", timestamp)]


batch = Table(
    "batch",
    metadata,
    *record_columns(),
    Column("experiment_id", Text),
    Column("baseline_batch_id", Text),
    Column("result_artifact", Sha256),
    Column("run_ids", ARRAY(Text)),
    Column("counts", JSONB(none_as_null=True)),
    Column("policy", JSONB(none_as_null=True)),
    Column("recorded_at", timestamp),
    *record_tail(),
)
triage_decision = Table(
    "triage_decision",
    metadata,
    *record_columns(),
    Column("dataset_id", Text),
    Column("model", Text),
    Column("probability", Float),
    Column("prompt_sha256", Text),
    Column("request_id", Text),
    Column("response_artifact", Sha256),
    Column("basis", Text),
    *record_tail(),
)
model_cache = Table(
    "model_cache",
    metadata,
    *record_columns(),
    Column("response_artifact", Sha256),
    Column("artifact_id", Sha256),
    *record_tail(),
)
model_call = Table(
    "model_call",
    metadata,
    *record_columns(),
    Column("experiment_id", Text),
    Column("caller_id", Text),
    Column("stage", Text),
    Column("model", Text),
    Column("status", Text),
    Column("input_tokens", BigInteger),
    Column("output_tokens", BigInteger),
    Column("reservation_usd", Float),
    Column("charge_usd", Float),
    Column("rate", JSONB(none_as_null=True)),
    *record_tail(),
)
event = Table(
    "event",
    metadata,
    *record_columns(),
    Column("at", timestamp),
    Column("experiment_id", Text),
    Column("stage", Text),
    Column("model", Text),
    Column("status", Text),
    Column("input_tokens", BigInteger),
    Column("output_tokens", BigInteger),
    Column("calculated_cost_usd", Float),
    Column("budget_charge_usd", Float),
    Column("wall_seconds", Float),
    *record_tail(),
)
evaluation = Table(
    "evaluation",
    metadata,
    *record_columns(),
    Column("worksheet_id", Text),
    Column("item_id", Text),
    Column("verdict", Text),
    Column("reviewer", Text),
    Column("evidence", Text),
    Column("review_type", Text),
    Column("labelled_at", timestamp),
    Column("batch_id", Text),
    *record_tail(),
)

artifact = catalog.artifact.c.sha256
batches = RecordTable(
    "batches",
    batch,
    [
        Field("experiment_id", "experiment_id", "text"),
        Field("baseline_batch_id", "baseline_batch_id", "text", references=batch.c.id),
        Field("result_artifact", "result_artifact", "sha256", references=artifact),
        Field("run_ids", "run_ids", "texts"),
        Field("counts", "counts", "json"),
        Field("policy", "policy", "json"),
        Field("created_at", "recorded_at", "timestamp"),
    ],
)
triage_decisions = RecordTable(
    "batches",
    triage_decision,
    [
        Field("dataset_id", "dataset_id", "text"),
        Field("model", "model", "text"),
        Field("probability", "probability", "float"),
        Field("prompt_sha256", "prompt_sha256", "text"),
        Field("request_id", "request_id", "text"),
        Field("response_artifact", "response_artifact", "sha256", references=artifact),
        Field("basis", "basis", "text"),
    ],
    append_only=True,
)
model_caches = RecordTable(
    "model cache",
    model_cache,
    [
        Field("response_artifact", "response_artifact", "sha256", references=artifact),
        Field("artifact_id", "artifact_id", "sha256", references=artifact),
    ],
    append_only=True,
)
model_calls = RecordTable(
    "budget_reservations",
    model_call,
    [
        Field("experiment_id", "experiment_id", "text"),
        Field("owner", "caller_id", "text"),
        Field("stage", "stage", "text"),
        Field("model", "model", "text"),
        Field("status", "status", "text"),
        Field("input_tokens", "input_tokens", "integer"),
        Field("output_tokens", "output_tokens", "integer"),
        Field("reservation_usd", "reservation_usd", "float"),
        Field("charge_usd", "charge_usd", "float"),
        Field("rate", "rate", "json"),
    ],
)
events = RecordTable(
    "events",
    event,
    [
        Field("at", "at", "timestamp"),
        Field("experiment_id", "experiment_id", "text"),
        Field("stage", "stage", "text"),
        Field("model", "model", "text"),
        Field("status", "status", "text"),
        Field("input_tokens", "input_tokens", "integer"),
        Field("output_tokens", "output_tokens", "integer"),
        Field("calculated_cost_usd", "calculated_cost_usd", "float"),
        Field("budget_charge_usd", "budget_charge_usd", "float"),
        Field("wall_seconds", "wall_seconds", "float"),
    ],
)
evaluations = RecordTable(
    "evaluations",
    evaluation,
    [
        Field("worksheet_id", "worksheet_id", "text"),
        Field("item_id", "item_id", "text"),
        Field("verdict", "verdict", "text"),
        Field("reviewer", "reviewer", "text"),
        Field("evidence", "evidence", "text"),
        Field("review_type", "review_type", "text"),
        Field("labelled_at", "labelled_at", "timestamp"),
        Field("batch_id", "batch_id", "text", references=batch.c.id),
    ],
)

# The store's `batches` table held three kinds of record. Cached responses and
# triage decisions are recognised by their key, so a lookup by key alone finds
# the right table; everything else is a batch.
BATCH_TABLES = (
    ("enhance-cache-", "enhancement_cache", model_caches),
    ("triage-", "triage_decision", triage_decisions),
)


def batch_table(key, kind=None):
    for prefix, table_kind, table in BATCH_TABLES:
        if key.startswith(prefix):
            return table
    for prefix, table_kind, table in BATCH_TABLES:
        if kind == table_kind:
            return table
    return batches


def batch_tables(kind=None):
    """The tables a listing of `batches` reads, given its kind filter."""
    if kind is None:
        return [batches, triage_decisions, model_caches]
    return [next((t for _, k, t in BATCH_TABLES if k == kind), batches)]


def charged(connection, owner, kind):
    """Budget charged by one owner's events of a kind."""
    return connection.execute(
        select(func.coalesce(func.sum(event.c.budget_charge_usd), 0)).where(
            event.c.owner_id == owner, event.c.kind == kind
        )
    ).scalar_one()


def put_embedding(connection, key, model, vector):
    """Store an embedding for similarity search. False if it is not storable.

    Only vectors of the indexed dimension are kept. An embedding that is already
    stored is left as it is.
    """
    if len(vector) != EMBEDDING_DIMENSIONS:
        return False
    connection.execute(
        text(
            "INSERT INTO ops.embedding (key, model, embedding) "
            "VALUES (:key, :model, CAST(:embedding AS vector)) ON CONFLICT DO NOTHING"
        ),
        {
            "key": key,
            "model": model,
            "embedding": "[" + ",".join(repr(float(v)) for v in vector) + "]",
        },
    )
    return True
