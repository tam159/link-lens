"""Store legacy payloads as jsonb so backfills can use JSON operators and indexes.

jsonb keeps every value but not the original text: object keys are reordered and
whitespace is dropped. Link Lens hashes with sorted keys, so stored IDs and hashes
are unaffected. The downgrade restores the json type, not the original key order.
Each table is rewritten under an exclusive lock; stop the pipeline first.
"""

from alembic import op

revision = "0006"
down_revision = "0005"
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
        op.execute(
            f"ALTER TABLE legacy.{table} "
            "ALTER COLUMN payload TYPE jsonb USING payload::jsonb"
        )


def downgrade():
    for table in reversed(TABLES):
        op.execute(
            f"ALTER TABLE legacy.{table} "
            "ALTER COLUMN payload TYPE json USING payload::json"
        )
