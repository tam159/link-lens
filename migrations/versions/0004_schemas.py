"""Create the production schemas. They stay empty until their phase."""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

SCHEMAS = [
    "ontology",
    "catalog",
    "onboarding",
    "evidence",
    "identity",
    "ops",
    "access",
    "serving",
    "legacy",
]


def upgrade():
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA {schema}")


def downgrade():
    # No CASCADE: a schema that still holds objects must fail the downgrade.
    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA {schema}")
