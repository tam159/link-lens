"""Record drift checks, and when each observation was loaded.

`catalog.drift_check` holds the result of comparing a snapshot with a mapping
config: unchanged, or changed with reasons. The result follows from the two, so
there is one row per snapshot and config and checking again writes nothing.

`evidence.observation.loaded_at` is when a row was stored. A release serves the
observations that were stored when it was recorded, so a later extraction, of
the same snapshot or a refreshed one, cannot add rows to a release that already
exists. Rows stored before this migration get the epoch: they were loaded
before anything was released. Adding the column rewrites no row.
"""

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        CREATE TABLE catalog.drift_check (
            snapshot_id text NOT NULL REFERENCES catalog.snapshot,
            config_hash sha256 NOT NULL REFERENCES onboarding.mapping_config,
            source_id   text NOT NULL REFERENCES catalog.source,
            status      text NOT NULL CHECK (status IN ('unchanged', 'changed')),
            -- The approved mapping cannot extract from this snapshot.
            blocking    boolean NOT NULL,
            reasons     jsonb NOT NULL,
            checked_at  timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (snapshot_id, config_hash)
        )
        """
    )
    op.execute("CREATE INDEX ON catalog.drift_check (source_id, checked_at)")
    op.execute(
        "CREATE TRIGGER forbid_update BEFORE UPDATE ON catalog.drift_check "
        "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
    )
    op.execute(
        "ALTER TABLE evidence.observation "
        "ADD COLUMN loaded_at timestamptz NOT NULL DEFAULT 'epoch'"
    )
    op.execute(
        "ALTER TABLE evidence.observation ALTER COLUMN loaded_at SET DEFAULT now()"
    )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # Views are dbt's and may read these; dbt builds them again.
    op.execute(
        """
        DO $do$
        DECLARE
            name text;
        BEGIN
            FOR name IN
                SELECT schemaname || '.' || quote_ident(viewname) FROM pg_views
                WHERE viewowner = 'linklens_transform'
            LOOP
                EXECUTE format('DROP VIEW IF EXISTS %s CASCADE', name);
            END LOOP;
        END
        $do$
        """
    )
    op.execute("ALTER TABLE evidence.observation DROP COLUMN loaded_at")
    op.execute("DROP TABLE catalog.drift_check")
