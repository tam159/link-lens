"""Alembic environment.

Migrations are explicit SQL (`op.execute`), so there is no target metadata and no
autogeneration. The database URL comes from, in order: a connection passed in
`config.attributes["connection"]`, the `sqlalchemy.url` option, then
`LINK_LENS_DATABASE_URL` through the application settings.
"""

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

config = context.config


def run(connection):
    # One transaction per migration: a failed step leaves earlier steps applied
    # and recorded, and a step may change role without affecting the next one.
    context.configure(
        connection=connection, target_metadata=None, transaction_per_migration=True
    )
    with context.begin_transaction():
        context.run_migrations()


supplied = config.attributes.get("connection")
if supplied is not None:
    run(supplied)
else:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        from link_lens.settings import settings

        url = settings().database_url
    engine = create_engine(url, poolclass=NullPool)
    with engine.connect() as connection:
        run(connection)
    engine.dispose()
