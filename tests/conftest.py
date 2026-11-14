"""Test fixtures.

Database tests run on PostgreSQL built by `alembic upgrade head`. The server is
started on first use, so a test that never touches the store needs no database.
By default it is a throwaway container; set `LINK_LENS_TEST_DATABASE_URL` to use
an existing server instead. Either way the tests create and drop their own
`linklens_test_*` databases and never use the database named in that URL.
"""

import os
import threading
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from link_lens import store
from link_lens.settings import settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "pgvector/pgvector:pg17-trixie"
SCHEMAS = (
    "ontology",
    "catalog",
    "onboarding",
    "evidence",
    "identity",
    "ops",
    "access",
    "serving",
    "legacy",
)


def migrate(url, revision="head", direction="upgrade"):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    getattr(command, direction)(config, revision)


class TestServer:
    """A PostgreSQL server for the session, started when a test first needs it."""

    __test__ = False

    def __init__(self):
        self._lock = threading.Lock()
        self._container = None
        self._server_url = None
        self._created = []
        self._engine = None
        self._reset = None

    def _server(self):
        if self._server_url is None:
            url = os.environ.get("LINK_LENS_TEST_DATABASE_URL")
            if not url:
                try:
                    from testcontainers.community.postgres import PostgresContainer

                    self._container = PostgresContainer(
                        IMAGE, driver="psycopg"
                    ).with_command(
                        "postgres -c fsync=off -c synchronous_commit=off "
                        "-c full_page_writes=off"
                    )
                    self._container.start()
                except Exception as error:
                    raise RuntimeError(
                        "Database tests need Docker to start a PostgreSQL container, "
                        "or LINK_LENS_TEST_DATABASE_URL pointing at a server with "
                        "the vector extension available"
                    ) from error
                url = self._container.get_connection_url()
            self._server_url = url
        return self._server_url

    def _admin(self, statement):
        engine = create_engine(
            self._server(), isolation_level="AUTOCOMMIT", poolclass=NullPool
        )
        with engine.connect() as connection:
            connection.execute(text(statement))

    def create_database(self):
        """Create an empty database on the server and return its URL."""
        name = "linklens_test_" + uuid.uuid4().hex[:12]
        self._admin(f'CREATE DATABASE "{name}"')
        self._created.append(name)
        return (
            make_url(self._server())
            .set(database=name)
            .render_as_string(hide_password=False)
        )

    def engine(self):
        """Engine on the shared, fully migrated database."""
        with self._lock:
            if self._engine is None:
                url = self.create_database()
                migrate(url)
                engine = create_engine(url, pool_pre_ping=True)
                with engine.connect() as connection:
                    tables = connection.execute(
                        text(
                            "SELECT quote_ident(schemaname) || '.' || "
                            "quote_ident(tablename) FROM pg_tables "
                            "WHERE schemaname = ANY(:schemas)"
                        ),
                        {"schemas": list(SCHEMAS)},
                    ).scalars()
                    self._reset = (
                        "TRUNCATE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"
                    )
                self._engine = engine
            return self._engine

    def reset(self):
        with self._engine.begin() as connection:
            connection.execute(text(self._reset))

    def stop(self):
        if self._engine is not None:
            self._engine.dispose()
        for name in self._created:
            self._admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        if self._container is not None:
            self._container.stop()


@pytest.fixture(scope="session")
def postgres_server():
    server = TestServer()
    yield server
    server.stop()


@pytest.fixture
def empty_database(postgres_server):
    """URL of a new database with no migrations applied."""
    return postgres_server.create_database()


@pytest.fixture
def database(isolated_store):
    """Engine on the migrated test database, for tests that use SQL directly."""
    return store.engine()


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch, postgres_server):
    # A test that reaches the database outside the fixture fails instead of
    # touching whatever LINK_LENS_DATABASE_URL or .env points at.
    monkeypatch.setenv("LINK_LENS_DATABASE_URL", "no-database-configured-for-tests://")
    monkeypatch.setenv("LINK_LENS_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    settings.cache_clear()
    used = []

    def engine():
        used.append(True)
        return postgres_server.engine()

    monkeypatch.setattr(store, "engine", engine)
    yield
    # Store calls commit on their own connections, hold an advisory lock on a
    # separate autocommit connection and run in worker threads, so a test cannot
    # be wrapped in one rolled-back transaction. Tables are emptied instead.
    if used:
        postgres_server.reset()
    settings.cache_clear()


@pytest.fixture
def spec():
    from link_lens.contracts import MappingSpec

    return MappingSpec.model_validate(
        {
            "reader": {"format": "csv"},
            "record_grain": "One row per legal entity",
            "subject_role": "legal_entity",
            "source_kind": "company_register",
            "subject_label_field": "name",
            "fields": [
                {
                    "source_fields": ["name"],
                    "canonical_field": "entity.legal_name",
                    "transformations": [{"op": "trim"}],
                    "confidence": 0.9,
                    "evidence": "Explicit legal entity name column",
                },
                {
                    "source_fields": ["abn"],
                    "canonical_field": "entity.abn",
                    "transformations": [{"op": "abn"}],
                    "confidence": 0.9,
                    "evidence": "Explicit ABN column with checksum validation",
                },
            ],
            "unmapped_fields": [],
            "source_reliability": 0.9,
            "limitations": ["Synthetic fixture, never a submitted agent config."],
        }
    )


@pytest.fixture
def snapshot():
    return {
        "id": "snapshot",
        "format": "csv",
        "source_id": "source-a",
        "observed_at": "2025-01-01T00:00:00Z",
        "observed_at_basis": "publication proxy",
        "receipt": {"retrieved_at": "2025-02-01T00:00:00Z"},
        "licence": "CC BY",
        "sha256": "a" * 64,
    }
