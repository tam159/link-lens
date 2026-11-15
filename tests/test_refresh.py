"""Refresh steps: download check, drift, extraction under an approved mapping, onboarding."""

import pytest
from link_lens import drift, ingestion, refresh, sources, store
from link_lens.contracts import content_hash
from link_lens.ingestion import new_run
from sqlalchemy import text

ABNS = ["51824753556", "53004085616", "11005357522"]


def csv_of(header, rows):
    return (
        "\n".join([",".join(header)] + [",".join(row) for row in rows]) + "\n"
    ).encode()


def snapshot_of(source_id, data, retrieved_at):
    artifact = store.blob(data, "text/csv", "fixture.csv")
    record = {
        "id": f"{source_id}-{artifact[:12]}",
        "source_id": source_id,
        "resource_id": "resource-1",
        "artifact_id": artifact,
        "sha256": artifact,
        "format": "csv",
        "receipt": {"retrieved_at": retrieved_at, "partial": False},
        "observed_at": "2025-01-01T00:00:00Z",
        "observed_at_basis": "publication proxy",
        "licence": "CC BY",
    }
    store.put("snapshots", record["id"], record, source_id, "snapshot", immutable=True)
    return record


def approve(spec, source_id, snapshot, name="mapping"):
    """A completed run of the source with an approved mapping. A test fixture."""
    run = new_run({"id": source_id, "slug": source_id}, snapshot)
    spec.ontology_hash = run["ontology_hash"]
    config_hash = content_hash(spec)
    mapping = {
        "id": f"{run['id']}:1",
        "run_id": run["id"],
        "config": spec.model_dump(),
        "config_hash": config_hash,
        "version": 1,
    }
    store.put("mappings", mapping["id"], mapping, run["id"])
    approval = {
        "id": f"{run['id']}-{name}-approval",
        "run_id": run["id"],
        "mapping_id": mapping["id"],
        "decision": "approved",
        "config_hash": config_hash,
        "reviewer": "TEST FIXTURE; NOT HUMAN EVALUATION",
    }
    store.put("approvals", approval["id"], approval, run["id"])
    run.update(status="completed", mapping_id=mapping["id"], approval_id=approval["id"])
    store.put("runs", run["id"], run, source_id, "onboarding")
    return run, config_hash


@pytest.fixture
def source(spec):
    """A registered source with one snapshot and an approved mapping for it."""
    source_id = "source-refresh"
    store.put(
        "sources",
        source_id,
        {
            "id": source_id,
            "slug": "refresh-fixture",
            "portal": "https://data.gov.au/data",
            "metadata": {"title": "Refresh fixture", "license_title": "CC BY"},
        },
        kind="registered",
    )
    rows = [[f"Entity {n}", abn] for n, abn in enumerate(ABNS)]
    snapshot = snapshot_of(
        source_id, csv_of(["name", "abn"], rows), "2025-02-01T00:00:00Z"
    )
    run, config_hash = approve(spec, source_id, snapshot)
    return {
        "id": source_id,
        "snapshot": snapshot,
        "run": run,
        "config_hash": config_hash,
    }


def count(sql, **parameters):
    with store.engine().connect() as connection:
        return connection.execute(text(sql), parameters).scalar_one()


def test_extracting_a_snapshot_twice_stores_it_once(source):
    assert (
        sources.state(source["id"])[0]["approved_config_hash"] == source["config_hash"]
    )
    first = refresh.extract(source["id"])
    assert (first["records"], first["observations"], first["inserted"]) == (3, 6, 6)
    assert first["snapshot_id"] == source["snapshot"]["id"]
    again = refresh.extract(source["id"])
    assert again["inserted"] == 0
    assert again["observation_digest"] == first["observation_digest"]
    assert count("SELECT count(*) FROM evidence.observation") == 6
    # A bound on the records read is respected and adds nothing new either.
    assert refresh.extract(source["id"], limit=2)["observations"] == 4


def test_a_source_without_an_approved_mapping_is_not_extracted(spec):
    store.put("sources", "bare", {"id": "bare", "slug": "bare"}, kind="registered")
    snapshot_of(
        "bare", csv_of(["name", "abn"], [["A", ABNS[0]]]), "2025-02-01T00:00:00Z"
    )
    checked = refresh.check_drift("bare")
    assert (checked["status"], checked["blocking"]) == ("no_approved_mapping", True)
    with pytest.raises(refresh.Blocked, match="no_approved_mapping"):
        refresh.extract("bare")
    assert count("SELECT count(*) FROM catalog.drift_check") == 0


def test_drift_stops_extraction_until_a_new_mapping_is_approved(source, spec):
    refresh.extract(source["id"])
    # The publisher renames a column the mapping uses.
    changed = snapshot_of(
        source["id"],
        csv_of(["legal_name", "abn"], [["Entity 9", ABNS[0]]]),
        "2025-03-01T00:00:00Z",
    )
    assert sources.state(source["id"])[0]["latest_snapshot_id"] == changed["id"]

    checked = refresh.check_drift(source["id"])
    assert (checked["status"], checked["blocking"]) == ("changed", True)
    assert {
        "kind": "missing_used_column",
        "column": "name",
        "blocking": True,
    } in checked["reasons"]
    # The result is stored once, however often it is asked for.
    assert refresh.check_drift(source["id"])["checked_at"] == checked["checked_at"]
    # One row for the first snapshot's check at extraction, one for this one.
    assert count("SELECT count(*) FROM catalog.drift_check") == 2
    with pytest.raises(refresh.Blocked, match="missing_used_column"):
        refresh.extract(source["id"])
    assert count("SELECT count(*) FROM evidence.observation") == 6
    # The earlier snapshot still fits and is still extractable.
    assert refresh.extract(source["id"], source["snapshot"]["id"])["inserted"] == 0

    # A person approves a mapping for the new shape; extraction resumes.
    spec.subject_label_field = "legal_name"
    spec.fields[0].source_fields = ["legal_name"]
    approve(spec, source["id"], changed, name="second")
    resumed = refresh.extract(source["id"])
    assert (resumed["snapshot_id"], resumed["records"], resumed["inserted"]) == (
        changed["id"],
        1,
        2,
    )
    assert count("SELECT count(*) FROM catalog.drift_check") == 3
    with (
        store.engine().connect() as connection,
        pytest.raises(Exception, match="append-only"),
    ):
        connection.execute(text("UPDATE catalog.drift_check SET blocking = false"))


def test_drift_record_matches_the_library_function(source):
    stored = drift.record(source["snapshot"]["id"], source["config_hash"])
    computed = drift.detect(source["snapshot"]["id"], source["config_hash"])
    assert (stored["status"], stored["blocking"], stored["reasons"]) == (
        computed["status"],
        computed["blocking"],
        computed["reasons"],
    )


class Client:
    """Stands in for the LangGraph server: records what it was asked to start."""

    def __init__(self):
        self.started = []
        self.threads = self.runs = self

    def create(self, *args, **options):
        if not args:
            return {"thread_id": f"thread-{len(self.started) + 1}"}
        self.started.append((args, options))
        return {"run_id": f"server-run-{len(self.started)}"}


def test_onboarding_is_requested_once_per_snapshot(source):
    changed = snapshot_of(
        source["id"],
        csv_of(["legal_name", "abn"], [["E", ABNS[0]]]),
        "2025-03-01T00:00:00Z",
    )
    client = Client()
    first = refresh.request_onboarding(source["id"], client)
    assert first["started"] and first["snapshot_id"] == changed["id"]
    run = store.require("runs", first["run_id"])
    assert (run["thread_id"], run["status"], run["snapshot_id"]) == (
        "thread-1",
        "new",
        changed["id"],
    )
    assert client.started[0][0] == ("thread-1", "onboard")
    assert client.started[0][1]["input"]["run_id"] == first["run_id"]
    # Asking again starts nothing: no second thread, no second run, no spend.
    again = refresh.request_onboarding(source["id"], client)
    assert (again["started"], again["run_id"]) == (False, first["run_id"])
    assert len(client.started) == 1
    # The snapshot that already has its approved run is left with it.
    assert not refresh.request_onboarding(
        source["id"], client, source["snapshot"]["id"]
    )["started"]


def test_check_reports_whether_the_bytes_changed(source, monkeypatch):
    asked = []

    def register(request):
        asked.append(request)
        return {"id": source["id"]}, store.require(
            "snapshots", source["snapshot"]["id"]
        )

    monkeypatch.setattr(ingestion, "register", register)
    result = refresh.check(source["id"])
    assert result["changed"] is False
    assert result["snapshot_id"] == result["previous_snapshot_id"]
    assert (asked[0].dataset_id, asked[0].resource_id) == (source["id"], "resource-1")


def test_cli_extracts_and_exits_3_when_blocked(source):
    import json

    from link_lens.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()
    done = runner.invoke(app, ["source", "extract", source["id"], "--limit", "2"])
    assert done.exit_code == 0 and json.loads(done.output)["inserted"] == 4
    snapshot_of(
        source["id"],
        csv_of(["legal_name", "abn"], [["E", ABNS[0]]]),
        "2025-03-01T00:00:00Z",
    )
    blocked = runner.invoke(app, ["source", "extract", source["id"]])
    assert blocked.exit_code == 3
    assert "missing_used_column" in json.loads(blocked.output)["blocked"]
