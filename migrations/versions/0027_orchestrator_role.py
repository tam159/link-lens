"""The role an orchestrator works as: the pipeline's rights without the human gates.

`linklens_orchestrator` reads and writes what the deterministic data flow
writes: snapshots, runs, drift checks, source records, observations, batches,
entities, links, profiles and usage. It cannot insert or change what only a
person records: a mapping approval, an ontology activation or promotion, a
release, a bundle scope or a bundle, a review label, or anything in `access`.
It has no use for `serving` or `analytics` and no access to them: dbt builds
those, as its own role.
So "no asset creates a release, an approval or a promotion" is a rule of the
database, whatever the orchestration code does.

A table created later in a core schema is writable by this role through default
privileges. A new table that records a human decision must revoke that itself.
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

ROLE = "linklens_orchestrator"
WRITE = ["ontology", "catalog", "onboarding", "evidence", "identity", "ops"]
READ = WRITE
# What only a person records.
HUMAN_GATES = [
    "onboarding.approval",
    "ontology.activation",
    "ops.release",
    "ops.bundle_scope",
    "ops.release_bundle",
    "ops.evaluation",
]


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
    for schema in READ:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {ROLE}")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {ROLE}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"GRANT SELECT ON TABLES TO {ROLE}"
        )
    for schema in WRITE:
        op.execute(f"GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA {schema} TO {ROLE}")
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {ROLE}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"GRANT INSERT, UPDATE ON TABLES TO {ROLE}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"GRANT USAGE, SELECT ON SEQUENCES TO {ROLE}"
        )
    for table in HUMAN_GATES:
        op.execute(f"REVOKE INSERT, UPDATE ON {table} FROM {ROLE}")


def downgrade():
    for schema in READ:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"REVOKE ALL ON TABLES FROM {ROLE}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE linklens_migrator IN SCHEMA {schema} "
            f"REVOKE ALL ON SEQUENCES FROM {ROLE}"
        )
    op.execute(f"DROP OWNED BY {ROLE}")
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
