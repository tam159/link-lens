"""Refresh facts of a source and the drift check against its approved mapping."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest
from link_lens import drift, ingestion, sources, store
from link_lens.cli import app
from link_lens.contracts import SourceRequest, content_hash
from typer.testing import CliRunner

SOURCE = "source-a"
CSV = b"name,abn,state\nAcme,51824753556,NSW\nBeta,51824753556,VIC\n"


def stored(
    spec, snapshot, data=CSV, source=SOURCE, retrieved="2026-03-01T00:00:00+00:00"
):
    """A source with a snapshot of `data`, and the mapping config for it."""
    blob = store.blob(data, "text/csv", "data.csv")
    store.put(
        "sources",
        source,
        {"id": source, "metadata": {"title": "Fixture"}},
        kind="registered",
    )
    snap = {
        **snapshot,
        "id": hashlib.sha256(source.encode() + data).hexdigest(),
        "source_id": source,
        "artifact_id": blob,
        "sha256": blob,
        "receipt": {"retrieved_at": retrieved, "partial": False},
    }
    store.put("snapshots", snap["id"], snap, source, "snapshot", immutable=True)
    config = spec.model_dump(mode="json")
    config["unmapped_fields"] = [{"source_field": "state", "reason": "Not needed"}]
    return snap, config


def approve(
    run_id, config, decision="approved", at="2026-03-02T00:00:00+00:00", source=SOURCE
):
    snapshot_id = store.listing("snapshots")[0]["id"]
    store.put(
        "runs", run_id, {"id": run_id, "source_id": source, "snapshot_id": snapshot_id}
    )
    mapping = {
        "id": run_id + ":1",
        "run_id": run_id,
        "config": config,
        "config_hash": content_hash(config),
    }
    store.put("mappings", mapping["id"], mapping, run_id, "mapping", immutable=True)
    approval = {
        "id": hashlib.sha256((run_id + decision).encode()).hexdigest(),
        "run_id": run_id,
        "mapping_id": mapping["id"],
        "config_hash": mapping["config_hash"],
        "decision": decision,
        "at": at,
    }
    store.put("approvals", approval["id"], approval, run_id, "approval", immutable=True)
    return mapping["config_hash"]


def test_state_reports_what_is_stored_and_what_is_derived(spec, snapshot):
    snap, config = stored(spec, snapshot)
    facts = sources.state(SOURCE)[0]
    assert facts == {
        "source_id": SOURCE,
        "kind": "registered",
        "title": "Fixture",
        "cadence_days": None,
        "last_checked_at": None,
        "next_check_due_at": None,
        "latest_snapshot_id": snap["id"],
        "last_changed_at": "2026-03-01T00:00:00+00:00",
        "approved_config_hash": None,
        "approved_mapping_id": None,
        "approved_run_id": None,
        "approved_at": None,
    }
    first = approve("run-1", config)
    assert sources.state(SOURCE)[0]["approved_config_hash"] == first
    # A later request for revision approves nothing; a later approval takes over.
    revised = {**config, "limitations": ["A revised mapping"]}
    approve(
        "run-2", revised, decision="revision_requested", at="2026-03-03T00:00:00+00:00"
    )
    assert sources.state(SOURCE)[0]["approved_run_id"] == "run-1"
    second = approve("run-3", revised, at="2026-03-04T00:00:00+00:00")
    facts = sources.state(SOURCE)[0]
    assert (facts["approved_config_hash"], facts["approved_run_id"]) == (
        second,
        "run-3",
    )
    assert (facts["approved_mapping_id"], facts["approved_at"]) == (
        "run-3:1",
        "2026-03-04T00:00:00+00:00",
    )
    assert second != first
    with pytest.raises(KeyError):
        sources.state("unknown-source")
    assert [f["source_id"] for f in sources.state(kind="registered")] == [SOURCE]
    assert sources.state(kind="catalogue") == []


def test_checks_and_cadence_are_recorded_once(spec, snapshot):
    stored(spec, snapshot)
    checked = sources.record_check(SOURCE, "2026-03-05T06:00:00+00:00")
    assert checked["last_checked_at"] == "2026-03-05T06:00:00+00:00"
    assert checked["next_check_due_at"] is None
    assert (
        sources.set_cadence(SOURCE, 7)["next_check_due_at"]
        == "2026-03-12T06:00:00+00:00"
    )

    def updated_at():
        from sqlalchemy import text

        with store.engine().connect() as connection:
            return connection.execute(
                text("SELECT updated_at FROM catalog.source_refresh")
            ).scalar_one()

    before = updated_at()
    # The same facts again, or an earlier check, write nothing.
    sources.record_check(SOURCE, "2026-03-05T06:00:00+00:00")
    sources.record_check(SOURCE, "2026-03-01T00:00:00+00:00")
    sources.set_cadence(SOURCE, 7)
    assert updated_at() == before
    assert sources.state(SOURCE)[0]["last_checked_at"] == "2026-03-05T06:00:00+00:00"
    assert (
        sources.record_check(SOURCE, datetime(2026, 3, 6, tzinfo=UTC))["cadence_days"]
        == 7
    )
    assert sources.set_cadence(SOURCE, None)["cadence_days"] is None
    with pytest.raises(ValueError, match="longer than zero"):
        sources.set_cadence(SOURCE, 0)


def test_registering_a_source_records_the_check_whether_or_not_bytes_changed(
    monkeypatch,
):
    dataset = {
        "id": "dataset-1",
        "name": "fixture-dataset",
        "license_title": "CC BY",
        "resources": [
            {
                "id": "resource-1",
                "format": "CSV",
                "url": "https://data.example.gov.au/file.csv",
                "last_modified": "2026-02-01T00:00:00",
            }
        ],
    }
    times = iter(["2026-03-01T00:00:00+00:00", "2026-03-08T00:00:00+00:00"])
    monkeypatch.setattr(ingestion, "action", lambda portal, name, **kw: dataset)
    monkeypatch.setattr(
        ingestion,
        "download",
        lambda url, **kw: (CSV, {"retrieved_at": next(times), "partial": False}),
    )
    request = SourceRequest(dataset_id="dataset-1", resource_id="resource-1")
    _, first = ingestion.register(request)
    _, second = ingestion.register(request)  # the publisher still serves the same bytes
    assert first["id"] == second["id"] and len(store.listing("snapshots")) == 1
    facts = sources.state("dataset-1")[0]
    assert facts["last_checked_at"] == "2026-03-08T00:00:00+00:00"
    assert facts["last_changed_at"] == "2026-03-01T00:00:00+00:00"
    assert facts["latest_snapshot_id"] == first["id"]


def test_compare_names_each_difference_and_whether_it_blocks(spec):
    config = spec.model_dump(mode="json")
    config["unmapped_fields"] = [{"source_field": "state", "reason": "Not needed"}]
    config["filters"] = [{"field": "status", "op": "nonempty"}]
    assert drift.expected(config) == (
        {"name", "abn", "status"},
        {"name", "abn", "status", "state"},
    )
    assert drift.compare(config, "csv", ["name", "abn", "status", "state"]) == {
        "status": "unchanged",
        "blocking": False,
        "reasons": [],
    }
    changed = drift.compare(config, "xlsx", ["name", "status", "postcode"])
    assert changed["status"] == "changed" and changed["blocking"]
    assert changed["reasons"] == [
        {
            "kind": "format",
            "blocking": True,
            "detail": "mapping reads csv, snapshot is xlsx",
        },
        {"kind": "missing_used_column", "column": "abn", "blocking": True},
        {"kind": "removed_unused_column", "column": "state", "blocking": False},
        {"kind": "new_column", "column": "postcode", "blocking": False},
    ]
    added = drift.compare(config, "csv", ["name", "abn", "status", "state", "postcode"])
    assert added["status"] == "changed" and not added["blocking"]


def test_detect_reads_the_snapshot_with_the_approved_reader(spec, snapshot):
    snap, config = stored(spec, snapshot)
    config_hash = approve("run-1", config)
    result = drift.detect(snap["id"], config_hash)
    assert result == {
        "snapshot_id": snap["id"],
        "config_hash": config_hash,
        "status": "unchanged",
        "blocking": False,
        "reasons": [],
    }
    renamed, _ = stored(
        spec, snapshot, data=b"name,ABN number,state,postcode\nAcme,1,NSW,2000\n"
    )
    kinds = [
        (r["kind"], r.get("column"))
        for r in drift.detect(renamed["id"], config_hash)["reasons"]
    ]
    assert kinds == [
        ("missing_used_column", "abn"),
        ("new_column", "ABN number"),
        ("new_column", "postcode"),
    ]
    workbook = {
        **config,
        "reader": {**config["reader"], "format": "xlsx", "sheet": "Data"},
    }
    unreadable = drift.detect(snap["id"], config=workbook)
    assert unreadable["blocking"] and unreadable["reasons"][0]["kind"] == "reader"
    with pytest.raises(KeyError):
        drift.detect(snap["id"], "ab" * 32)


def test_cli_reports_state_and_exits_3_on_blocking_drift(spec, snapshot):
    runner = CliRunner()
    snap, config = stored(spec, snapshot)
    assert (
        runner.invoke(app, ["source", "drift", SOURCE]).exit_code == 2
    )  # nothing approved
    approve("run-1", config)
    state = json.loads(
        runner.invoke(app, ["source", "state", "--source-id", SOURCE]).output
    )
    assert state[0]["latest_snapshot_id"] == snap["id"]
    assert (
        json.loads(
            runner.invoke(app, ["source", "cadence", SOURCE, "--days", "1"]).output
        )["cadence_days"]
        == 1
    )
    assert (
        runner.invoke(app, ["source", "cadence", SOURCE, "--days", "-1"]).exit_code == 2
    )
    unchanged = runner.invoke(app, ["source", "drift", SOURCE])
    assert (
        unchanged.exit_code == 0
        and json.loads(unchanged.output)["status"] == "unchanged"
    )
    later = (datetime(2026, 3, 9, tzinfo=UTC) + timedelta(0)).isoformat()
    stored(spec, snapshot, data=b"name,state\nAcme,NSW\n", retrieved=later)
    blocked = runner.invoke(app, ["source", "drift", SOURCE])
    assert blocked.exit_code == 3
    assert json.loads(blocked.output)["reasons"][0] == {
        "kind": "missing_used_column",
        "column": "abn",
        "blocking": True,
    }
    assert (
        runner.invoke(
            app, ["source", "drift", SOURCE, "--snapshot-id", snap["id"]]
        ).exit_code
        == 0
    )
