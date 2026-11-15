"""Define the three database roles as NOLOGIN privilege groups.

linklens_migrator owns the schemas and runs DDL. linklens_pipeline reads and
writes the core schemas and, until the legacy tables are retired, `legacy`.
linklens_product reads `serving`; its write on `access.api_usage` is granted
with that table. Passwords are not set here: a deployment creates login roles
and grants one of these to each.

Table privileges are default privileges of linklens_migrator, so they apply to
tables that role creates. Later migrations create their objects with
`SET LOCAL ROLE linklens_migrator`. DELETE is not granted by default.

Roles are shared by every database in a cluster. The downgrade removes this
database's grants and drops a role only when no other database still uses it.
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

ROLES = ["linklens_migrator", "linklens_pipeline", "linklens_product"]
CORE = ["ontology", "catalog", "onboarding", "evidence", "identity", "ops", "access"]
SCHEMAS = CORE + ["serving", "legacy"]
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
VERSION_TABLE = "public.alembic_version"


def upgrade():
    for role in ROLES:
        op.execute(
            f"""
            DO $do$
            BEGIN
                CREATE ROLE {role} NOLOGIN;
            EXCEPTION WHEN duplicate_object THEN
                NULL;
            END
            $do$
            """
        )
    for schema in SCHEMAS:
        op.execute(f"ALTER SCHEMA {schema} OWNER TO linklens_migrator")
    for table in TABLES:
        op.execute(f"ALTER TABLE legacy.{table} OWNER TO linklens_migrator")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON {VERSION_TABLE} TO linklens_migrator"
    )

    for schema in CORE + ["legacy"]:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO linklens_pipeline")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA legacy "
        "TO linklens_pipeline"
    )
    for schema in CORE:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            "GRANT SELECT, INSERT, UPDATE ON TABLES TO linklens_pipeline"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            "GRANT USAGE, SELECT ON SEQUENCES TO linklens_pipeline"
        )

    op.execute("GRANT USAGE ON SCHEMA serving TO linklens_product")
    op.execute("GRANT USAGE ON SCHEMA access TO linklens_product")
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA serving "
        "GRANT SELECT ON TABLES TO linklens_product"
    )


def downgrade():
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA serving "
        "REVOKE SELECT ON TABLES FROM linklens_product"
    )
    op.execute("REVOKE USAGE ON SCHEMA access FROM linklens_product")
    op.execute("REVOKE USAGE ON SCHEMA serving FROM linklens_product")

    for schema in CORE:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            "REVOKE USAGE, SELECT ON SEQUENCES FROM linklens_pipeline"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            "REVOKE SELECT, INSERT, UPDATE ON TABLES FROM linklens_pipeline"
        )
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA legacy "
        "FROM linklens_pipeline"
    )
    for schema in CORE + ["legacy"]:
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM linklens_pipeline")

    op.execute(f"REVOKE ALL ON {VERSION_TABLE} FROM linklens_migrator")
    for table in TABLES:
        op.execute(f"ALTER TABLE legacy.{table} OWNER TO CURRENT_USER")
    for schema in SCHEMAS:
        op.execute(f"ALTER SCHEMA {schema} OWNER TO CURRENT_USER")
    for role in reversed(ROLES):
        op.execute(
            f"""
            DO $do$
            BEGIN
                DROP ROLE {role};
            EXCEPTION WHEN dependent_objects_still_exist THEN
                RAISE NOTICE 'role {role} is still used by another database; kept';
            END
            $do$
            """
        )
