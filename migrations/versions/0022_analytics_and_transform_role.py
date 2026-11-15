"""The analytics schema, and the role dbt works as.

`analytics` holds internal reporting relations. Alembic owns the schema and its
grants; dbt creates every relation inside it and Alembic none. Nothing in it is
served to clients: the product role has no access to it.

`linklens_transform` is a NOLOGIN group like the other three roles. It reads the
core schemas and `serving`, and may create relations only in `analytics`. It
does not read `legacy`, which is history no new code should depend on, nor the
hash of a key's secret or the rate buckets in `access`. `CREATE` on `serving`
is not granted here: dbt takes over the serving views in a later migration.

The downgrade drops whatever the role owns in this database, which is only
relations dbt built and can build again.
"""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

ROLE = "linklens_transform"
# Schemas the role reads whole, including tables the migrator creates later.
READ = ["ontology", "catalog", "onboarding", "evidence", "identity", "ops", "serving"]
ACCESS_TABLES = "access.tier, access.client, access.api_usage"
# Every column of a key except key_hash.
KEY_COLUMNS = "id, client_id, prefix, label, created_at, expires_at, revoked_at"


def upgrade():
    op.execute(
        f"""
        DO $do$
        BEGIN
            CREATE ROLE {ROLE} NOLOGIN;
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END
        $do$
        """
    )
    op.execute("CREATE SCHEMA analytics AUTHORIZATION linklens_migrator")
    op.execute(f"GRANT USAGE, CREATE ON SCHEMA analytics TO {ROLE}")
    for schema in READ:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {ROLE}")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {ROLE}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"GRANT SELECT ON TABLES TO {ROLE}"
        )
    op.execute(f"GRANT USAGE ON SCHEMA access TO {ROLE}")
    op.execute(f"GRANT SELECT ON {ACCESS_TABLES} TO {ROLE}")
    op.execute(f"GRANT SELECT ({KEY_COLUMNS}) ON access.api_key TO {ROLE}")


def downgrade():
    for schema in READ:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"REVOKE SELECT ON TABLES FROM {ROLE}"
        )
    # Relations dbt built, and every privilege granted to the role here.
    op.execute(f"DROP OWNED BY {ROLE}")
    # No CASCADE: anything left in the schema was not dbt's and must be looked at.
    op.execute("DROP SCHEMA analytics")
    op.execute(
        f"""
        DO $do$
        BEGIN
            DROP ROLE {ROLE};
        EXCEPTION WHEN dependent_objects_still_exist THEN
            RAISE NOTICE 'role {ROLE} is still used by another database; kept';
        END
        $do$
        """
    )
