"""Evidence: source records and observations, partitioned by source.

An observation references its source record, its concept and the mapping config
it was extracted with. Licence, snapshot, roles and source reliability are read
through those references instead of being copied onto each row. Both tables are
append-only. A source gets its own partitions through
`evidence.ensure_source_partitions`; rows of other sources use the defaults.
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

DDL = [
    """
    CREATE TABLE evidence.source_record (
        source_id   text NOT NULL REFERENCES catalog.source,
        id          sha256 NOT NULL,
        snapshot_id text NOT NULL REFERENCES catalog.snapshot,
        sheet       text,
        row_no      bigint,
        locator     jsonb NOT NULL,
        PRIMARY KEY (source_id, id)
    ) PARTITION BY LIST (source_id)
    """,
    "CREATE TABLE evidence.source_record_default PARTITION OF evidence.source_record DEFAULT",
    "CREATE INDEX ON evidence.source_record (snapshot_id)",
    """
    CREATE TABLE evidence.observation (
        source_id        text NOT NULL,
        id               sha256 NOT NULL,
        record_id        sha256 NOT NULL,
        concept_id       bigint NOT NULL REFERENCES ontology.concept,
        config_hash      sha256 NOT NULL REFERENCES onboarding.mapping_config,
        group_name       text,
        group_id         sha256,
        value            text NOT NULL,
        raw_value        jsonb NOT NULL,
        source_fields    text[] NOT NULL,
        field_confidence double precision NOT NULL,
        observed_at      timestamptz NOT NULL,
        timestamp_basis  text NOT NULL CHECK (timestamp_basis IN ('snapshot', 'record')),
        timezone_assumed boolean NOT NULL,
        ingested_at      timestamptz NOT NULL,
        derivation_level text NOT NULL,
        engine           text NOT NULL,
        extra            jsonb NOT NULL DEFAULT '{}',
        PRIMARY KEY (source_id, id),
        FOREIGN KEY (source_id, record_id)
            REFERENCES evidence.source_record (source_id, id),
        CHECK ((group_name IS NULL) = (group_id IS NULL))
    ) PARTITION BY LIST (source_id)
    """,
    "CREATE TABLE evidence.observation_default PARTITION OF evidence.observation DEFAULT",
    "CREATE INDEX ON evidence.observation (source_id, record_id)",
    # Values can be long; the index holds a prefix so no value is too large for it.
    "CREATE INDEX ON evidence.observation (concept_id, left(value, 256))",
    "CREATE INDEX ON evidence.observation (config_hash)",
    """
    CREATE FUNCTION evidence.ensure_source_partitions(source text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $function$
    DECLARE
        suffix text := substr(md5(source), 1, 16);
    BEGIN
        -- Rows already in a default partition stay there: a new partition
        -- could not be created over them.
        IF EXISTS (SELECT 1 FROM evidence.source_record_default WHERE source_id = source)
           OR EXISTS (SELECT 1 FROM evidence.observation_default WHERE source_id = source)
        THEN
            RETURN;
        END IF;
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS evidence.%I PARTITION OF evidence.source_record FOR VALUES IN (%L)',
            'source_record_' || suffix, source);
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS evidence.%I PARTITION OF evidence.observation FOR VALUES IN (%L)',
            'observation_' || suffix, source);
    END
    $function$
    """,
    "REVOKE ALL ON FUNCTION evidence.ensure_source_partitions(text) FROM PUBLIC",
    "GRANT EXECUTE ON FUNCTION evidence.ensure_source_partitions(text) TO linklens_pipeline",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in ("source_record", "observation"):
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON evidence.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("DROP FUNCTION evidence.ensure_source_partitions(text)")
    op.execute("DROP TABLE evidence.observation")
    op.execute("DROP TABLE evidence.source_record")
