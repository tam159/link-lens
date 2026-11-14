"""Releases and the per-release OKF tables.

A release is a human record that one batch, under one ontology version, is what
clients see. It is append-only. The OKF page, line and index tables are built
once when a release is created and never change; each release has its own
partitions, created through `serving.create_release_partitions`, so a release
can be dropped when it leaves the retention window.

The serving views are not created here. Each is one SELECT in
`src/link_lens/serving/`, applied after every upgrade, so a view's definition
lives in one place.
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

OKF_TABLES = ["okf_page", "okf_line", "okf_index"]
DDL = [
    """
    CREATE TABLE ops.release (
        id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        batch_id      text NOT NULL REFERENCES ops.batch,
        ontology_hash sha256 NOT NULL REFERENCES ontology.ontology_version,
        released_by   text NOT NULL CHECK (released_by <> ''),
        released_at   timestamptz NOT NULL DEFAULT now(),
        notes         text
    )
    """,
    """
    CREATE TABLE serving.okf_page (
        release_id            bigint NOT NULL REFERENCES ops.release,
        path                  text NOT NULL,
        type                  text NOT NULL,
        title                 text NOT NULL,
        description           text NOT NULL,
        tags                  text[] NOT NULL,
        status                text,
        entity_id             text,
        source_id             text,
        observation_source_id text,
        observation_id        sha256,
        concept_name          text,
        PRIMARY KEY (release_id, path)
    ) PARTITION BY LIST (release_id)
    """,
    "CREATE INDEX ON serving.okf_page (release_id, path text_pattern_ops)",
    "CREATE INDEX ON serving.okf_page (release_id, type)",
    "CREATE INDEX ON serving.okf_page USING gin (tags)",
    """
    CREATE TABLE serving.okf_line (
        release_id bigint NOT NULL REFERENCES ops.release,
        path       text NOT NULL,
        line_no    integer NOT NULL,
        line       text NOT NULL,
        source_id  text,
        PRIMARY KEY (release_id, path, line_no)
    ) PARTITION BY LIST (release_id)
    """,
    "CREATE INDEX ON serving.okf_line (release_id, path text_pattern_ops)",
    "CREATE INDEX ON serving.okf_line USING gin (line gin_trgm_ops)",
    "CREATE INDEX ON serving.okf_line USING gin (to_tsvector('simple', line))",
    """
    CREATE TABLE serving.okf_index (
        release_id  bigint NOT NULL REFERENCES ops.release,
        parent      text NOT NULL,
        position    integer NOT NULL,
        label       text NOT NULL,
        target      text NOT NULL,
        is_folder   boolean NOT NULL,
        entry_count integer NOT NULL,
        description text NOT NULL,
        source_id   text,
        PRIMARY KEY (release_id, parent, position)
    ) PARTITION BY LIST (release_id)
    """,
    """
    CREATE FUNCTION serving.create_release_partitions(release bigint) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $function$
    DECLARE
        name text;
    BEGIN
        FOREACH name IN ARRAY ARRAY['okf_page', 'okf_line', 'okf_index'] LOOP
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS serving.%I PARTITION OF serving.%I FOR VALUES IN (%s)',
                name || '_r' || release, name, release);
        END LOOP;
    END
    $function$
    """,
    "REVOKE ALL ON FUNCTION serving.create_release_partitions(bigint) FROM PUBLIC",
    "GRANT EXECUTE ON FUNCTION serving.create_release_partitions(bigint) TO linklens_pipeline",
    "GRANT USAGE ON SCHEMA serving TO linklens_pipeline",
    # The pipeline builds a release's OKF rows; the product role only reads them.
    "ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA serving "
    "GRANT SELECT, INSERT ON TABLES TO linklens_pipeline",
    "GRANT SELECT, INSERT ON serving.okf_page, serving.okf_line, serving.okf_index "
    "TO linklens_pipeline",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in ["ops.release"] + ["serving." + t for t in OKF_TABLES]:
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # Serving views are applied outside migrations and may depend on ops.release.
    op.execute(
        """
        DO $do$
        DECLARE
            name text;
        BEGIN
            FOR name IN SELECT viewname FROM pg_views WHERE schemaname = 'serving' LOOP
                EXECUTE format('DROP VIEW serving.%I', name);
            END LOOP;
        END
        $do$
        """
    )
    op.execute("DROP FUNCTION serving.create_release_partitions(bigint)")
    for table in reversed(OKF_TABLES):
        op.execute(f"DROP TABLE serving.{table}")
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA serving "
        "REVOKE SELECT, INSERT ON TABLES FROM linklens_pipeline"
    )
    op.execute("REVOKE USAGE ON SCHEMA serving FROM linklens_pipeline")
    op.execute("DROP TABLE ops.release")
