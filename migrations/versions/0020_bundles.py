"""Release bundles: named scopes and the archives built for a release.

A bundle scope is a named, bounded list of entities chosen by a person, such as
`demo`. A release bundle is one archive of a release's OKF files, for a named
scope or for one client; its bytes are an artifact and its manifest hash names
exactly what it holds. Bundle rows are append-only: building the same content
again adds nothing, and a scope that changed adds a new row.
"""

from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

DDL = [
    """
    CREATE TABLE ops.bundle_scope (
        name       text PRIMARY KEY CHECK (name ~ '^[a-z][a-z0-9-]{0,39}$'),
        entity_ids text[] NOT NULL CHECK (cardinality(entity_ids) BETWEEN 1 AND 500),
        -- Built without a command when a release is created.
        on_release boolean NOT NULL DEFAULT true,
        set_by     text NOT NULL CHECK (set_by <> ''),
        set_at     timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE ops.release_bundle (
        id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        release_id    bigint NOT NULL REFERENCES ops.release,
        scope         text NOT NULL,
        client_id     uuid REFERENCES access.client,
        -- The sources the files are limited to; null means every source.
        source_scope  text[],
        entity_count  integer NOT NULL,
        file_count    integer NOT NULL,
        size_bytes    bigint NOT NULL,
        artifact_sha  sha256 NOT NULL REFERENCES catalog.artifact,
        manifest_sha  sha256 NOT NULL,
        created_at    timestamptz NOT NULL DEFAULT now(),
        UNIQUE (release_id, scope, manifest_sha)
    )
    """,
    "CREATE INDEX ON ops.release_bundle (release_id, client_id)",
    "CREATE TRIGGER forbid_update BEFORE UPDATE ON ops.release_bundle "
    "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # A serving view reads the bundle table; views are applied again from their files.
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
    op.execute("DROP TABLE ops.release_bundle")
    op.execute("DROP TABLE ops.bundle_scope")
