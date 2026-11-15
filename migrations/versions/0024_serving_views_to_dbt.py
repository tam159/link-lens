"""Hand the serving views over to dbt.

Until now each serving view was created from a SQL file by the migrator, after
every upgrade. From here the views are dbt models in `transform/models/serving`
and belong to `linklens_transform`. This migration drops the views the migrator
owns and lets the transform role create in `serving`; `link-lens dbt build`
then builds them. Between the two steps `serving` has no views, so stop the
product service first.

The three `okf_*` tables and the functions in `serving` stay with Alembic:
they are not views and are not touched here.

The downgrade drops the views dbt built. The code before this migration
creates its own again when it upgrades to its head.
"""

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

DROP_VIEWS_OF = """
    DO $do$
    DECLARE
        name text;
    BEGIN
        FOR name IN
            SELECT viewname FROM pg_views
            WHERE schemaname = 'serving' AND viewowner = '{owner}'
        LOOP
            EXECUTE format('DROP VIEW serving.%I CASCADE', name);
        END LOOP;
    END
    $do$
"""


def upgrade():
    op.execute(DROP_VIEWS_OF.format(owner="linklens_migrator"))
    op.execute("GRANT CREATE ON SCHEMA serving TO linklens_transform")


def downgrade():
    # CASCADE: anything built on a serving view is a dbt relation too.
    op.execute(DROP_VIEWS_OF.format(owner="linklens_transform"))
    op.execute("REVOKE CREATE ON SCHEMA serving FROM linklens_transform")
