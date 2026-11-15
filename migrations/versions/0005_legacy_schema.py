"""Move the 17 generic tables from public to legacy. Indexes move with them."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABLES = [
    "sources",
    "snapshots",
    "runs",
    "mappings",
    "approvals",
    "observations",
    "entities",
    "memberships",
    "links",
    "profiles",
    "evaluations",
    "artifacts",
    "events",
    "batches",
    "ontologies",
    "ontology_events",
    "budget_reservations",
]


def upgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA legacy")


def downgrade():
    for table in reversed(TABLES):
        op.execute(f"ALTER TABLE legacy.{table} SET SCHEMA public")
