"""Database access for the product service, always as the product role."""

from contextlib import contextmanager

from sqlalchemy import text

from .. import store


@contextmanager
def session():
    """One transaction as `linklens_product`, whatever role the service logs in as.

    The role can read `serving`, read the access tables and count usage. It
    cannot read a core schema, so a mistake in a query cannot leak one.
    """
    with store.engine().begin() as connection:
        connection.execute(text("SET LOCAL ROLE linklens_product"))
        yield connection
