"""Operations: batches, triage decisions, model cache, model calls, events,
evaluations and embeddings.

These tables keep the store's record exactly, as the catalog and onboarding
tables do. Triage decisions, cached model responses and embeddings are
append-only. A model call is written when it is reserved and changed once when
it is settled; after that the database refuses to change it. A usage event is
written when a call starts and completed when it ends, so an interrupted call
leaves its receipt. An evaluation row is the current label for an item; every
label ever submitted is an event.
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

HEAD = """
        id         text PRIMARY KEY,
        owner_id   text NOT NULL DEFAULT '',
        kind       text NOT NULL DEFAULT '',"""
TAIL = """
        extra      jsonb NOT NULL DEFAULT '{}',
        created_at timestamptz NOT NULL DEFAULT now()"""
DDL = [
    f"""
    CREATE TABLE ops.batch ({HEAD}
        experiment_id     text,
        baseline_batch_id text REFERENCES ops.batch,
        result_artifact   sha256 REFERENCES catalog.artifact,
        run_ids           text[],
        counts            jsonb,
        policy            jsonb,
        recorded_at       timestamptz,{TAIL}
    )
    """,
    "CREATE INDEX ON ops.batch (kind)",
    f"""
    CREATE TABLE ops.triage_decision ({HEAD}
        dataset_id        text,
        model             text,
        probability       double precision,
        prompt_sha256     text,
        request_id        text,
        response_artifact sha256 REFERENCES catalog.artifact,
        basis             text,{TAIL}
    )
    """,
    "CREATE INDEX ON ops.triage_decision (owner_id)",
    f"""
    CREATE TABLE ops.model_cache ({HEAD}
        response_artifact sha256 REFERENCES catalog.artifact,
        artifact_id       sha256 REFERENCES catalog.artifact,{TAIL}
    )
    """,
    f"""
    CREATE TABLE ops.model_call ({HEAD}
        experiment_id   text,
        caller_id       text,
        stage           text,
        model           text,
        status          text,
        input_tokens    bigint,
        output_tokens   bigint,
        reservation_usd double precision,
        charge_usd      double precision,
        rate            jsonb,{TAIL}
    )
    """,
    "CREATE INDEX ON ops.model_call (owner_id)",
    """
    CREATE FUNCTION ops.forbid_change_after_settlement() RETURNS trigger
    LANGUAGE plpgsql AS $function$
    BEGIN
        IF OLD.status IN ('settled', 'historical_estimate') THEN
            RAISE EXCEPTION 'model call % is % and can no longer change', OLD.id, OLD.status
                USING ERRCODE = 'restrict_violation';
        END IF;
        RETURN NEW;
    END
    $function$
    """,
    """
    CREATE TRIGGER forbid_change_after_settlement BEFORE UPDATE ON ops.model_call
    FOR EACH ROW EXECUTE FUNCTION ops.forbid_change_after_settlement()
    """,
    f"""
    CREATE TABLE ops.event ({HEAD}
        at                  timestamptz,
        experiment_id       text,
        stage               text,
        model               text,
        status              text,
        input_tokens        bigint,
        output_tokens       bigint,
        calculated_cost_usd double precision,
        budget_charge_usd   double precision,
        wall_seconds        double precision,{TAIL}
    )
    """,
    "CREATE INDEX ON ops.event (owner_id, kind)",
    "CREATE INDEX ON ops.event (kind, created_at)",
    f"""
    CREATE TABLE ops.evaluation ({HEAD}
        worksheet_id text,
        item_id      text,
        verdict      text,
        reviewer     text,
        evidence     text,
        review_type  text,
        labelled_at  timestamptz,
        batch_id     text REFERENCES ops.batch,{TAIL}
    )
    """,
    "CREATE INDEX ON ops.evaluation (owner_id, kind)",
    "CREATE INDEX ON ops.evaluation (kind)",
    """
    CREATE TABLE ops.embedding (
        key        text PRIMARY KEY,
        model      text NOT NULL,
        embedding  vector(1536) NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON ops.embedding USING hnsw (embedding vector_cosine_ops)",
]
APPEND_ONLY = ["triage_decision", "model_cache", "embedding"]
TABLES = [
    "embedding",
    "evaluation",
    "event",
    "model_call",
    "model_cache",
    "triage_decision",
    "batch",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON ops.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for table in TABLES:
        op.execute(f"DROP TABLE ops.{table}")
    op.execute("DROP FUNCTION ops.forbid_change_after_settlement()")
