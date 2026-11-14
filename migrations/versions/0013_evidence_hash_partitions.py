"""Partition source records and observations by hash of the source, not by source.

One list partition per source does not suit thousands of sources. Both tables
become 32 hash partitions on `source_id`: a source's rows stay together in one
partition, the two tables stay aligned, and the number of partitions no longer
grows with the number of sources. Rows are copied, counted and only then are the
old tables dropped. `evidence.ensure_source_partitions` is no longer needed.
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

PARTITIONS = 32
OLD_INDEXES = [
    "source_record_pkey",
    "source_record_snapshot_id_idx",
    "observation_pkey",
    "observation_source_id_record_id_idx",
    "observation_concept_id_left_idx",
    "observation_config_hash_idx",
]
SOURCE_RECORD = """
    CREATE TABLE evidence.source_record (
        source_id   text NOT NULL REFERENCES catalog.source,
        id          sha256 NOT NULL,
        snapshot_id text NOT NULL REFERENCES catalog.snapshot,
        sheet       text,
        row_no      bigint,
        locator     jsonb NOT NULL,
        PRIMARY KEY (source_id, id)
    ) PARTITION BY {method} (source_id)
"""
OBSERVATION = """
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
        extra            jsonb NOT NULL DEFAULT '{{}}',
        PRIMARY KEY (source_id, id),
        FOREIGN KEY (source_id, record_id)
            REFERENCES evidence.source_record (source_id, id),
        CHECK ((group_name IS NULL) = (group_id IS NULL))
    ) PARTITION BY {method} (source_id)
"""
INDEXES = [
    "CREATE INDEX ON evidence.source_record (snapshot_id)",
    "CREATE INDEX ON evidence.observation (source_id, record_id)",
    # Values can be long; the index holds a prefix so no value is too large for it.
    "CREATE INDEX ON evidence.observation (concept_id, left(value, 256))",
    "CREATE INDEX ON evidence.observation (config_hash)",
]
ENSURE_PARTITIONS = """
    CREATE FUNCTION evidence.ensure_source_partitions(source text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $function$
    DECLARE
        suffix text := substr(md5(source), 1, 16);
    BEGIN
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
"""


def set_aside():
    """Rename the current tables and their indexes out of the way."""
    for index in OLD_INDEXES:
        op.execute(f"ALTER INDEX evidence.{index} RENAME TO previous_{index}")
    for table in ("observation", "source_record"):
        op.execute(f"ALTER TABLE evidence.{table} RENAME TO previous_{table}")


def copy_and_drop():
    """Copy every row into the new tables, check the counts, drop the old tables."""
    for table in ("source_record", "observation"):
        op.execute(
            f"INSERT INTO evidence.{table} SELECT * FROM evidence.previous_{table}"
        )
    for statement in INDEXES:
        op.execute(statement)
    op.execute(
        """
        DO $do$
        BEGIN
            IF (SELECT count(*) FROM evidence.observation)
                   <> (SELECT count(*) FROM evidence.previous_observation)
               OR (SELECT count(*) FROM evidence.source_record)
                   <> (SELECT count(*) FROM evidence.previous_source_record)
            THEN
                RAISE EXCEPTION 'row counts differ after repartitioning';
            END IF;
        END
        $do$
        """
    )
    for table in ("observation", "source_record"):
        op.execute(f"DROP TABLE evidence.previous_{table}")
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON evidence.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("DROP FUNCTION evidence.ensure_source_partitions(text)")
    set_aside()
    for table, ddl in (("source_record", SOURCE_RECORD), ("observation", OBSERVATION)):
        op.execute(ddl.format(method="HASH"))
        for remainder in range(PARTITIONS):
            op.execute(
                f"CREATE TABLE evidence.{table}_h{remainder:02d} "
                f"PARTITION OF evidence.{table} "
                f"FOR VALUES WITH (MODULUS {PARTITIONS}, REMAINDER {remainder})"
            )
    copy_and_drop()


def downgrade():
    # Rows return to the default list partitions; per-source partitions are
    # created again only when a source is registered.
    op.execute("SET LOCAL ROLE linklens_migrator")
    set_aside()
    for table, ddl in (("source_record", SOURCE_RECORD), ("observation", OBSERVATION)):
        op.execute(ddl.format(method="LIST"))
        op.execute(
            f"CREATE TABLE evidence.{table}_default "
            f"PARTITION OF evidence.{table} DEFAULT"
        )
    copy_and_drop()
    op.execute(ENSURE_PARTITIONS)
    op.execute(
        "REVOKE ALL ON FUNCTION evidence.ensure_source_partitions(text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION evidence.ensure_source_partitions(text) "
        "TO linklens_pipeline"
    )
