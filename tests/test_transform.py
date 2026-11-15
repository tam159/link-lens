"""The dbt project: it parses, connects as its own role and builds only where it may.

The tests that run dbt need the `transform` dependency group and are skipped
without it. They run on the migrated test database, never on a configured one.
"""

import json
from pathlib import Path

import pytest
from link_lens import transform
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "transform"

needs_dbt = pytest.mark.skipif(
    transform.executable() is None, reason="needs the transform dependency group"
)


def test_environment_comes_from_the_database_url():
    assert transform.environment(
        "postgresql+psycopg://reader:p%40ss%2Fword@db.internal:6543/linklens_copy"
    ) == {
        "LINK_LENS_DBT_HOST": "db.internal",
        "LINK_LENS_DBT_PORT": "6543",
        "LINK_LENS_DBT_USER": "reader",
        "LINK_LENS_DBT_PASSWORD": "p@ss/word",
        "LINK_LENS_DBT_DATABASE": "linklens_copy",
    }
    assert transform.environment("postgresql://u@h/d")["LINK_LENS_DBT_PORT"] == "5432"


def test_a_missing_project_is_reported(tmp_path):
    if transform.executable() is None:
        pytest.skip("needs the transform dependency group")
    with pytest.raises(FileNotFoundError, match="No dbt project"):
        transform.run(["parse"], url="postgresql://u@h/d", project_dir=tmp_path)


@pytest.fixture
def dbt(database, tmp_path):
    """Run a dbt command on the test database; returns its exit code and output."""
    url = database.url.render_as_string(hide_password=False)

    def run(*arguments):
        finished = transform.run(
            list(arguments),
            url=url,
            project_dir=PROJECT,
            # Keep dbt's build files and logs out of the repository.
            env={
                "DBT_TARGET_PATH": str(tmp_path / "target"),
                "DBT_LOG_PATH": str(tmp_path / "logs"),
            },
            capture_output=True,
            text=True,
        )
        return finished.returncode, finished.stdout + finished.stderr

    return run


@needs_dbt
def test_dbt_connects_as_the_transform_role(dbt):
    code, output = dbt("debug")
    assert code == 0, output
    assert "All checks passed" in output

    code, output = dbt(
        "show",
        "--quiet",
        "--output",
        "json",
        "--inline",
        "select current_user::text as role, current_database()::text as database",
    )
    assert code == 0, output
    row = json.loads(output[output.index("{") :])["show"][0]
    assert row["role"] == "linklens_transform"
    assert row["database"].startswith("linklens_test_")


@needs_dbt
def test_dbt_parses_and_builds_without_touching_other_schemas(dbt, database):
    owned = text(
        "SELECT n.nspname, c.relname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "JOIN pg_roles r ON r.oid = c.relowner WHERE r.rolname = :role "
        "ORDER BY 1, 2"
    )
    relations = text(
        "SELECT n.nspname, c.relname, r.rolname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "JOIN pg_roles r ON r.oid = c.relowner "
        "WHERE n.nspname NOT LIKE 'pg\\_%' AND n.nspname <> 'information_schema' "
        "ORDER BY 1, 2"
    )
    with database.connect() as connection:
        before = connection.execute(relations).all()

    code, output = dbt("parse")
    assert code == 0, output
    code, output = dbt("build")
    assert code == 0, output

    with database.connect() as connection:
        # Alembic and dbt never manage the same relation: whatever dbt owns is
        # in a schema it was given, and nothing Alembic made has changed hands.
        built = connection.execute(owned, {"role": "linklens_transform"}).all()
        assert {schema for schema, _ in built} <= {"analytics"}
        after = connection.execute(relations).all()
        assert [row for row in after if row.nspname != "analytics"] == [
            row for row in before if row.nspname != "analytics"
        ]


def test_the_profile_holds_no_secret_and_names_the_role():
    profile = (PROJECT / "profiles.yml").read_text()
    assert "role: linklens_transform" in profile
    for line in profile.splitlines():
        if line.strip().startswith("password:"):
            assert "env_var(" in line
