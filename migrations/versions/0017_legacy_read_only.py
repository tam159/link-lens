"""Make the legacy tables read-only for the pipeline role.

Every domain is now served from typed schemas, so the pipeline has no reason to
write the generic tables. They stay readable as the record of what was migrated.
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "REVOKE INSERT, UPDATE ON ALL TABLES IN SCHEMA legacy FROM linklens_pipeline"
    )


def downgrade():
    op.execute(
        "GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA legacy TO linklens_pipeline"
    )
