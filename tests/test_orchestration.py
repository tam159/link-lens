"""The Dagster code location loads, and its instance keeps its storage apart.

These tests need the `orchestration` dependency group and are skipped without it.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

dagster = pytest.importorskip(
    "dagster", reason="needs the orchestration dependency group"
)

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATION = ROOT / "orchestration"


def test_definitions_load(tmp_path):
    """What CI runs: every code location of the workspace loads without error."""
    finished = subprocess.run(
        [
            str(Path(sys.executable).parent / "dagster"),
            "definitions",
            "validate",
            "--workspace",
            str(ORCHESTRATION / "workspace.yaml"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert finished.returncode == 0, finished.stdout + finished.stderr
    assert "Validation successful for code location link_lens" in (
        finished.stdout + finished.stderr
    )


def test_code_location_imports_as_a_package(monkeypatch):
    monkeypatch.syspath_prepend(str(ORCHESTRATION))
    from link_lens_dagster import definitions

    assert isinstance(definitions.defs, dagster.Definitions)
    dagster.Definitions.validate_loadable(definitions.defs)


def test_instance_storage_is_its_own_database_and_holds_no_secret():
    config = yaml.safe_load((ORCHESTRATION / "dagster.yaml").read_text())
    database = config["storage"]["postgres"]["postgres_db"]
    # Every connection value comes from the environment, the password included.
    assert all(set(value) == {"env"} for value in database.values())
    assert config["telemetry"] == {"enabled": False}
    assert config["nux"] == {"enabled": False}

    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    for name in ("dagster-webserver", "dagster-daemon"):
        service = compose[name]
        assert service["profiles"] == ["orchestration"]
        assert service["environment"]["DAGSTER_POSTGRES_DB"] == "dagster"
        assert service["environment"]["DAGSTER_POSTGRES_USER"] == "dagster"
    # The default stack is what it was: these services start only with the profile.
    assert {name for name, service in compose.items() if "profiles" not in service} == {
        "postgres",
        "backend",
        "product",
        "frontend",
        "sandbox-controller",
    }


def test_dagster_sees_the_dbt_project():
    dagster_dbt = pytest.importorskip("dagster_dbt")
    project = dagster_dbt.DbtProject(project_dir=ROOT / "transform")
    assert project.project_dir == ROOT / "transform"
    assert project.name == "link_lens"
