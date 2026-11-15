"""A place to build serving views before clients read them: `serving_next`.

dbt builds the serving read models here first. `link-lens serving-compare`
then checks them, release by release, against what `serving` holds. Only after
that does a build go to `serving`. Nothing reads this schema but that check:
the product role has no access to it.
"""

from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA serving_next AUTHORIZATION linklens_migrator")
    op.execute("GRANT USAGE, CREATE ON SCHEMA serving_next TO linklens_transform")
    # The comparison reads both schemas as the pipeline.
    op.execute("GRANT USAGE ON SCHEMA serving_next TO linklens_pipeline")


def downgrade():
    # Whatever is here is a candidate dbt built and can build again.
    op.execute(
        """
        DO $do$
        DECLARE
            name text;
        BEGIN
            FOR name IN SELECT viewname FROM pg_views WHERE schemaname = 'serving_next' LOOP
                EXECUTE format('DROP VIEW serving_next.%I CASCADE', name);
            END LOOP;
        END
        $do$
        """
    )
    op.execute("DROP SCHEMA serving_next")
