"""Alembic migrations: an empty database, existing rows, and the head schema."""

import json

import pytest
from conftest import SCHEMAS, head_revision, migrate
from link_lens import store
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

PAYLOAD = {
    "zeta": 1,
    "alpha": {"nested": [1, 2.5, None, True], "text": "Café “quoted” 東京"},
    "score": 0.30000000000000004,
    "large": 12345678901234567890,
    "empty": {},
}


def scalars(connection, sql, **parameters):
    return list(connection.execute(text(sql), parameters).scalars())


def user_objects(connection):
    return {
        "schemas": scalars(
            connection,
            "SELECT nspname FROM pg_namespace WHERE nspname = ANY(:names)",
            names=list(SCHEMAS),
        ),
        "tables": scalars(
            connection,
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
            "AND tablename <> 'alembic_version'",
        ),
        "extensions": scalars(
            connection, "SELECT extname FROM pg_extension WHERE extname <> 'plpgsql'"
        ),
        "types": scalars(
            connection,
            "SELECT typname FROM pg_type WHERE typname = 'sha256'",
        ),
        "functions": scalars(
            connection,
            "SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace",
        ),
        "default_privileges": scalars(
            connection, "SELECT count(*) FROM pg_default_acl"
        ),
    }


def test_upgrade_and_downgrade_round_trip_on_empty_database(empty_database):
    engine = create_engine(empty_database, poolclass=NullPool)
    migrate(empty_database)
    with engine.connect() as connection:
        assert scalars(connection, "SELECT version_num FROM alembic_version") == [
            head_revision()
        ]
    migrate(empty_database, "base", "downgrade")
    with engine.connect() as connection:
        assert user_objects(connection) == {
            "schemas": [],
            "tables": [],
            "extensions": [],
            "types": [],
            "functions": [],
            "default_privileges": [0],
        }
    migrate(empty_database)
    with engine.connect() as connection:
        assert (
            len(
                scalars(
                    connection, "SELECT 1 FROM pg_tables WHERE schemaname = 'legacy'"
                )
            )
            == 17
        )


def test_existing_rows_survive_upgrade_and_downgrade(empty_database):
    engine = create_engine(empty_database, poolclass=NullPool)
    migrate(empty_database, "0002")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO runs (id, owner_id, kind, payload, created_at) "
                "VALUES ('run-1', 'source-1', 'onboarding', :payload, now())"
            ),
            {"payload": json.dumps(PAYLOAD, ensure_ascii=False)},
        )
        created = connection.execute(text("SELECT created_at FROM runs")).scalar_one()

    migrate(empty_database)
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT id, owner_id, kind, payload, created_at FROM legacy.runs")
        ).one()
        assert (row.id, row.owner_id, row.kind) == ("run-1", "source-1", "onboarding")
        assert row.payload == PAYLOAD
        assert row.created_at == created
        assert scalars(
            connection,
            "SELECT payload->'alpha'->>'text' FROM legacy.runs "
            "WHERE payload @> CAST(:probe AS jsonb)",
            probe='{"zeta": 1}',
        ) == [PAYLOAD["alpha"]["text"]]
        assert sorted(
            scalars(
                connection,
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'legacy' AND tablename = 'runs'",
            )
        ) == ["ix_runs_kind", "ix_runs_owner_id", "runs_pkey"]

    migrate(empty_database, "0002", "downgrade")
    with engine.connect() as connection:
        row = connection.execute(text("SELECT payload, created_at FROM runs")).one()
        assert row.payload == PAYLOAD
        assert row.created_at == created
        assert scalars(
            connection,
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'runs' "
            "AND column_name = 'payload'",
        ) == ["json"]


def test_head_schema(database):
    with database.connect() as connection:
        assert sorted(
            scalars(
                connection,
                "SELECT nspname FROM pg_namespace WHERE nspname = ANY(:names)",
                names=list(SCHEMAS),
            )
        ) == sorted(SCHEMAS)
        assert {"vector", "pg_trgm"} <= set(
            scalars(connection, "SELECT extname FROM pg_extension")
        )
        columns = connection.execute(
            text(
                "SELECT table_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'legacy' AND column_name = 'payload'"
            )
        ).all()
        assert {c.table_name for c in columns} == set(store.TABLES)
        assert {c.data_type for c in columns} == {"jsonb"}
        assert scalars(
            connection,
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
        ) == ["alembic_version"]


def test_sha256_domain_holds_exactly_32_bytes(database):
    digest = "ab" * 32
    with database.connect() as connection:
        assert scalars(
            connection,
            "SELECT sha256_hex(sha256_from_hex(:digest))",
            digest=digest,
        ) == [digest]
        assert scalars(connection, "SELECT NULL::sha256 IS NULL") == [True]
        with pytest.raises(DBAPIError, match="sha256"):
            connection.execute(text("SELECT decode('abcd', 'hex')::sha256"))


def test_forbid_update_rejects_updates_and_allows_inserts(database):
    with database.connect() as connection:
        connection.execute(text("CREATE TEMP TABLE claims (id int, value text)"))
        connection.execute(
            text(
                "CREATE TRIGGER forbid_update BEFORE UPDATE ON claims "
                "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
            )
        )
        connection.execute(text("INSERT INTO claims VALUES (1, 'first')"))
        with pytest.raises(DBAPIError, match="append-only") as error:
            with connection.begin_nested():
                connection.execute(text("UPDATE claims SET value = 'changed'"))
        assert error.value.orig.sqlstate == "23001"
        connection.execute(text("INSERT INTO claims VALUES (2, 'second')"))
        assert scalars(connection, "SELECT value FROM claims ORDER BY id") == [
            "first",
            "second",
        ]
        connection.rollback()


def allowed(connection, role, sql):
    """Whether `role` may run `sql`. Nothing the statement does is kept."""
    try:
        with connection.begin_nested() as savepoint:
            connection.execute(text(f"SET LOCAL ROLE {role}"))
            connection.execute(text(sql))
            savepoint.rollback()
        return True
    except DBAPIError as error:
        if error.orig.sqlstate != "42501":  # insufficient_privilege
            raise
        return False


def test_roles_have_only_their_privileges(database):
    insert = (
        "INSERT INTO {} (id, owner_id, kind, payload, created_at) "
        "VALUES ('x', '', '', '{{}}', now())"
    )
    with database.connect() as connection:
        assert scalars(
            connection,
            "SELECT rolcanlogin FROM pg_roles WHERE rolname LIKE 'linklens\\_%'",
        ) == [False, False, False]

        # Every domain is typed now: the pipeline role may read legacy rows only.
        assert allowed(connection, "linklens_pipeline", "SELECT * FROM legacy.runs")
        assert not allowed(
            connection, "linklens_pipeline", insert.format("legacy.runs")
        )
        assert not allowed(
            connection, "linklens_pipeline", "UPDATE legacy.runs SET kind = ''"
        )
        assert not allowed(connection, "linklens_pipeline", "DELETE FROM legacy.runs")
        assert not allowed(connection, "linklens_product", "SELECT * FROM legacy.runs")

        # Tables the migrator creates later inherit the default privileges.
        connection.execute(text("SET LOCAL ROLE linklens_migrator"))
        for schema in ("ops", "serving"):
            connection.execute(
                text(
                    f"CREATE TABLE {schema}.probe (id bigint GENERATED ALWAYS AS "
                    "IDENTITY PRIMARY KEY, note text)"
                )
            )
        connection.execute(text("RESET ROLE"))
        write = "INSERT INTO {}.probe (note) VALUES ('x')"
        read = "SELECT * FROM {}.probe"
        assert allowed(connection, "linklens_pipeline", write.format("ops"))
        assert allowed(connection, "linklens_pipeline", read.format("ops"))
        assert not allowed(connection, "linklens_pipeline", "DELETE FROM ops.probe")
        # The pipeline builds a release's OKF rows in serving but never edits them.
        assert allowed(connection, "linklens_pipeline", read.format("serving"))
        assert not allowed(
            connection, "linklens_pipeline", "UPDATE serving.probe SET note = 'y'"
        )
        assert allowed(connection, "linklens_product", read.format("serving"))
        assert not allowed(connection, "linklens_product", write.format("serving"))
        assert not allowed(connection, "linklens_product", read.format("ops"))
        assert not allowed(
            connection, "linklens_pipeline", "CREATE TABLE ops.other (id int)"
        )
        connection.rollback()


def test_each_recent_migration_steps_down_and_up_again(empty_database):
    """A partial downgrade leaves the serving views dropped; head restores them."""
    from link_lens import serving

    engine = create_engine(empty_database, poolclass=NullPool)
    migrate(empty_database)
    views = "SELECT viewname FROM pg_views WHERE schemaname = 'serving'"
    with engine.connect() as connection:
        assert sorted(scalars(connection, views)) == sorted(serving.MODELS)
    for revision in ("-1", "0018", "0017"):
        migrate(empty_database, revision, "downgrade")
        with engine.connect() as connection:
            assert scalars(connection, views) == []
        migrate(empty_database)
        with engine.connect() as connection:
            assert sorted(scalars(connection, views)) == sorted(serving.MODELS)
