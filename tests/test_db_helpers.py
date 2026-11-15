"""The sha256 column type and the COPY-based bulk loader."""

from datetime import UTC, datetime

import pytest
from link_lens.db import Sha256, copy_insert
from sqlalchemy import BigInteger, Column, DateTime, MetaData, Table, Text, select, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.exc import StatementError

claims = Table(
    "claims",
    MetaData(),
    Column("id", Sha256, primary_key=True),
    Column("serial", BigInteger),
    Column("parent", Sha256),
    Column("value", Text),
    Column("raw_value", JSONB),
    Column("source_fields", ARRAY(Text)),
    Column("observed_at", DateTime(timezone=True)),
    Column("note", Text),
)


@pytest.fixture
def connection(database):
    with database.connect() as connection:
        connection.execute(
            text(
                """
                CREATE TEMP TABLE claims (
                    id sha256 PRIMARY KEY,
                    serial bigint GENERATED ALWAYS AS IDENTITY,
                    parent sha256,
                    value text,
                    raw_value jsonb NOT NULL,
                    source_fields text[] NOT NULL,
                    observed_at timestamptz,
                    note text NOT NULL DEFAULT 'defaulted'
                )
                """
            )
        )
        yield connection
        connection.rollback()


def key(number):
    return f"{number:064x}"


def row(number):
    return {
        "id": key(number),
        "parent": key(number - 1) if number % 2 else None,
        "value": f"tab\there, newline\nthere, backslash \\ and Café {number}",
        "raw_value": {"n": number, "list": [1, None], "text": "東京"},
        "source_fields": ["name", "with, comma"],
        "observed_at": datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC),
    }


COLUMNS = ["id", "parent", "value", "raw_value", "source_fields", "observed_at"]


def test_sha256_presents_hex_and_stores_bytes(connection):
    connection.execute(
        claims.insert().values(
            id=key(255), parent=None, raw_value={}, source_fields=[], note="n"
        )
    )
    assert connection.execute(select(claims.c.id, claims.c.parent)).one() == (
        key(255),
        None,
    )
    assert (
        connection.execute(
            select(claims.c.note).where(claims.c.id == key(255))
        ).scalar_one()
        == "n"
    )
    assert connection.execute(
        text("SELECT octet_length(id), sha256_hex(id) FROM claims")
    ).one() == (32, key(255))


@pytest.mark.parametrize("value", ["ab", "AB" * 32, "zz" * 32, b"\x00" * 32, 7])
def test_sha256_rejects_anything_but_lowercase_hex_digests(connection, value):
    with pytest.raises(StatementError, match="64 lowercase hex"):
        connection.execute(select(claims.c.id).where(claims.c.id == value))


def test_copy_insert_loads_rows_and_is_idempotent(connection):
    rows = [row(n) for n in range(1, 501)]
    assert copy_insert(connection, claims, rows, COLUMNS) == 500
    assert copy_insert(connection, claims, rows, COLUMNS) == 0

    stored = (
        connection.execute(select(claims).where(claims.c.id == key(7))).mappings().one()
    )
    assert {name: stored[name] for name in COLUMNS} == row(7)
    assert stored["note"] == "defaulted"
    assert stored["serial"] is not None
    assert connection.execute(
        text("SELECT count(*), count(parent) FROM claims")
    ).one() == (500, 250)


def test_copy_insert_keeps_existing_rows_and_adds_only_new_ones(connection):
    assert copy_insert(connection, claims, [row(1), row(2)], COLUMNS) == 2
    changed = {**row(2), "value": "a later load must not overwrite"}
    # Row 3 appears twice in one load; the first occurrence is kept.
    load = [changed, row(3), {**row(3), "value": "duplicate"}, row(4)]
    assert copy_insert(connection, claims, load, COLUMNS) == 2
    values = dict(connection.execute(select(claims.c.id, claims.c.value)).all())
    assert values == {key(n): row(n)["value"] for n in (1, 2, 3, 4)}
    assert (
        connection.execute(
            text("SELECT count(*) FROM pg_tables WHERE tablename LIKE 'copy_insert_%'")
        ).scalar_one()
        == 0
    )


def test_copy_insert_accepts_an_empty_load_and_a_generator(connection):
    assert copy_insert(connection, claims, [], COLUMNS) == 0
    assert copy_insert(connection, claims, (row(n) for n in range(3)), COLUMNS) == 3
