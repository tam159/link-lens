"""A read role for the team and the dashboard tool: `linklens_analyst`.

`analytics` holds internal reporting models built by dbt. This role may use
that schema and nothing else; dbt grants it SELECT on the models meant to be
read, in `transform/dbt_project.yml`. It is a NOLOGIN group like the others: a
person or a dashboard tool gets a login that is a member of it. The product
role still has no access to `analytics`.
"""

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

ROLE = "linklens_analyst"


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
    op.execute(f"GRANT USAGE ON SCHEMA analytics TO {ROLE}")


def downgrade():
    # Every privilege granted to the role in this database, dbt's grants included.
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
