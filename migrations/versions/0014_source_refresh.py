"""Refresh facts for each source, for an orchestrator to read.

`source_refresh` holds what cannot be derived: the intended cadence and when the
publisher was last checked. `source_state` adds what the other tables already
say: the latest snapshot and when the bytes last changed, and the approved
mapping in force, which is the most recent approved config among the source's
runs. Nothing here is a second copy of a fact stored elsewhere.
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        CREATE TABLE catalog.source_refresh (
            source_id       text PRIMARY KEY REFERENCES catalog.source,
            cadence         interval CHECK (cadence > interval '0'),
            last_checked_at timestamptz,
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE VIEW catalog.source_state AS
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
               approved.approved_at
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
    )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("DROP VIEW catalog.source_state")
    op.execute("DROP TABLE catalog.source_refresh")
