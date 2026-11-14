"""The migration baseline: stable digests, change detection and read-only access."""

import importlib.util
import json
from pathlib import Path

import pytest
from link_lens import store
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

spec = importlib.util.spec_from_file_location(
    "migration_baseline",
    Path(__file__).resolve().parents[1] / "scripts" / "migration_baseline.py",
)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def observation(number, config_hash, record):
    return {
        "id": f"obs-{number}",
        "config_hash": config_hash,
        "source_id": "source-a",
        "source_record_id": record,
    }


def legacy_put(table, key, payload, owner="", kind=""):
    """Write a generic row directly: the baseline describes the legacy tables."""
    from datetime import UTC, datetime

    from sqlalchemy.dialects.postgresql import insert

    statement = insert(store.TABLES[table]).values(
        id=key, owner_id=owner, kind=kind, payload=payload, created_at=datetime.now(UTC)
    )
    with store.engine().begin() as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["id"], set_={"payload": payload}
            )
        )


def legacy_count(table):
    from sqlalchemy import func, select

    with store.engine().connect() as connection:
        return connection.execute(
            select(func.count()).select_from(store.TABLES[table])
        ).scalar_one()


@pytest.fixture
def url(database):
    legacy_put("ontologies", "hash-1", {"id": "hash-1"}, kind="ontology")
    legacy_put("runs", "run-new", {"experiment_id": "exp-2"}, "source-a", "onboarding")
    legacy_put("runs", "run-old", {}, "source-a", "onboarding")
    for run, config in [("run-new", "config-new"), ("run-old", "config-old")]:
        legacy_put(
            "mappings",
            run + ":1",
            {"config_hash": config, "run_id": run},
            run,
            "mapping",
        )
    # Extraction stored an observation under its run, assembly under its source.
    legacy_put("observations", "obs-1", observation(1, "config-new", "r1"), "run-new")
    legacy_put("observations", "obs-2", observation(2, "config-new", "r1"), "source-a")
    legacy_put("observations", "obs-3", observation(3, "config-old", "r2"), "run-old")
    legacy_put("batches", "batch-1", {"run_ids": ["run-new"]}, kind="pipeline")
    legacy_put(
        "profiles",
        "batch-1:entity-1",
        {"profile_version": "version-1"},
        "batch-1",
        "profile",
    )
    return database.url.render_as_string(hide_password=False)


def test_baseline_counts_by_experiment_and_batch(url):
    result = script.baseline(url)
    assert result["environment"]["schema"] == "legacy"
    assert result["tables"]["observations"]["rows"] == 3
    assert result["tables"]["observations"]["kinds"][""]["owners"]["run-new"] == {
        "rows": 1,
        "ids": script.digest(["obs-1"]),
    }
    new, old = result["experiments"]["exp-2"], result["experiments"][script.UNSET]
    assert new["observations"] == script.summary(["obs-1", "obs-2"])
    assert new["source_records"]["count"] == 1
    assert old["observations"] == script.summary(["obs-3"])
    batch = result["batches"]["batch-1"]
    assert batch["experiments"] == ["exp-2"]
    assert batch["observations"]["count"] == 2
    assert batch["profile_versions"] == script.summary(["batch-1:entity-1:version-1"])
    assert result["digests"]["observation_ids"] == script.summary(
        ["obs-1", "obs-2", "obs-3"]
    )
    assert result["digests"]["record_ids"]["count"] == 2
    assert result["digests"]["observations_without_mapping"]["count"] == 0


def test_second_run_is_identical_and_changes_are_reported(url, tmp_path, capsys):
    output = tmp_path / "baseline.json"
    arguments = ["--database-url", url, "--output", str(output)]
    assert script.main(arguments) == 0
    saved = json.loads(output.read_text())
    assert script.comparable(saved) == script.comparable(script.baseline(url))
    assert script.main(arguments + ["--check", str(output)]) == 0
    with pytest.raises(SystemExit):
        script.main(arguments)  # an existing baseline is not replaced silently

    legacy_put("observations", "obs-4", observation(4, "config-old", "r3"), "run-old")
    legacy_put("runs", "run-old", {"status": "changed"}, "source-a", "onboarding")
    assert script.main(arguments + ["--check", str(output)]) == 1
    reported = capsys.readouterr().out
    assert "/digests/observation_ids" in reported
    assert "/tables/runs/payloads" in reported
    assert "/tables/runs/ids" not in reported
    assert json.loads(output.read_text()) == saved


def test_baseline_cannot_write(url, monkeypatch):
    def write(connection):
        connection.execute(text("DELETE FROM legacy.observations"))

    monkeypatch.setattr(script, "collect", write)
    with pytest.raises(DBAPIError, match="read-only"):
        script.baseline(url)
    assert legacy_count("observations") == 3
