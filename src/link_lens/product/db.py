"""Database access for the product service, always as the product role.

Two kinds of transaction. `writer` is on the primary: it authenticates, applies
limits and counts the call, so a revoked key or a spent quota takes effect at
once. `session` reads data, from the replica when one is configured. Without
product URLs both use the one configured database, as in local development.
"""

from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text

from .. import store
from ..settings import settings


@lru_cache
def dedicated(url):
    return create_engine(url, pool_pre_ping=True)


def primary():
    url = settings().product_database_url
    return dedicated(url) if url else store.engine()


def replica():
    url = settings().product_replica_url
    return dedicated(url) if url else primary()


@contextmanager
def transaction(engine):
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL ROLE linklens_product"))
        yield connection


def session():
    """One read transaction as `linklens_product`, whatever role the service logs in as.

    The role can read `serving`, read the access tables and count usage. It
    cannot read a core schema, so a mistake in a query cannot leak one.
    """
    return transaction(replica())


def writer():
    """One transaction on the primary, for the key, the limits and the count."""
    return transaction(primary())
