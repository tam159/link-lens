"""What a schedule needs to know about a source: paused, and failing.

`catalog.source_refresh` gains when a source was paused and by whom, and how
many checks in a row have failed with the time and reason of the last one, so
a schedule can leave a paused source alone and back off from a publisher that
is not answering. `catalog.source_state` shows them. Cadence, pause and the
failure count are data; an orchestrator reads them and keeps no copy.
"""

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

STATE = """
    CREATE OR REPLACE VIEW catalog.source_state AS
    SELECT s.id AS source_id,
           s.kind,
           s.title,
           r.cadence,
           r.last_checked_at,
           r.last_checked_at + r.cadence AS next_check_due_at,
           latest.id AS latest_snapshot_id,
           latest.changed_at AS last_changed_at,
           approved.config_hash AS approved_config_hash,
           approved.mapping_id AS approved_mapping_id,
           approved.run_id AS approved_run_id,
           approved.approved_at{extra}
    FROM catalog.source s
    LEFT JOIN catalog.source_refresh r ON r.source_id = s.id
    LEFT JOIN LATERAL (
        SELECT snapshot.id,
               coalesce(snapshot.retrieved_at, snapshot.created_at) AS changed_at
        FROM catalog.snapshot
        WHERE snapshot.source_id = s.id
        ORDER BY 2 DESC, snapshot.id DESC
        LIMIT 1
    ) latest ON true
    LEFT JOIN LATERAL (
        SELECT approval.config_hash,
               approval.mapping_id,
               approval.run_id,
               coalesce(approval.decided_at, approval.created_at) AS approved_at
        FROM onboarding.approval
        JOIN onboarding.run ON run.id = approval.run_id
        WHERE run.source_id = s.id
          AND approval.decision = 'approved'
          AND approval.config_hash IS NOT NULL
        ORDER BY 4 DESC, approval.id DESC
        LIMIT 1
    ) approved ON true
"""
# New columns go last: a view can be replaced in place only that way.
EXTRA = """,
           r.paused_at,
           r.paused_by,
           coalesce(r.consecutive_failures, 0) AS consecutive_failures,
           r.last_failure_at,
           r.last_error,
           -- After a failure, wait an hour, then two, then four, up to the cadence.
           CASE WHEN coalesce(r.consecutive_failures, 0) > 0 THEN
               r.last_failure_at + LEAST(
                   coalesce(r.cadence, interval '1 day'),
                   interval '1 hour' * power(2, LEAST(r.consecutive_failures, 10) - 1)
               )
           END AS retry_after"""


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        ALTER TABLE catalog.source_refresh
            ADD COLUMN paused_at timestamptz,
            ADD COLUMN paused_by text,
            ADD COLUMN consecutive_failures integer NOT NULL DEFAULT 0
                CHECK (consecutive_failures >= 0),
            ADD COLUMN last_failure_at timestamptz,
            ADD COLUMN last_error text,
            ADD CONSTRAINT paused_by_someone CHECK ((paused_at IS NULL) = (paused_by IS NULL))
        """
    )
    op.execute(STATE.format(extra=EXTRA))


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # A view cannot lose columns in place, and dbt's views read this one.
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
    op.execute("DROP VIEW catalog.source_state")
    op.execute(STATE.format(extra=""))
    op.execute(
        """
        ALTER TABLE catalog.source_refresh
            DROP CONSTRAINT paused_by_someone,
            DROP COLUMN paused_at,
            DROP COLUMN paused_by,
            DROP COLUMN consecutive_failures,
            DROP COLUMN last_failure_at,
            DROP COLUMN last_error
        """
    )
