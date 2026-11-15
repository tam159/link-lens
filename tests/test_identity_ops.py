"""Typed identity and operations tables behind the store facade."""

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from link_lens import backfill, budget, cli, logs, store
from link_lens.contracts import content_hash
from link_lens.db import evidence, identity, ops
from link_lens.db.records import same
from link_lens.extraction import valid_abn
from link_lens.ingestion import new_run
from link_lens.pipeline import assemble
from link_lens.readers import partition, record
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError
from test_evidence_spine import chain, claims

LEGACY_NAMES = (
    "batches",
    "budget_reservations",
    "events",
    "evaluations",
    "entities",
    "memberships",
    "links",
    "profiles",
)


def count(table, *where):
    with store.engine().connect() as connection:
        return connection.execute(
            select(func.count()).select_from(table).where(*where)
        ).scalar_one()


def assembled(spec, snapshot, sources=("source-a", "source-b")):
    """Approved runs for sources that share fifty entities, ready to assemble."""
    ids, number = [], 10000000000
    while len(ids) < 50:
        if valid_abn(str(number)):
            ids.append(str(number))
        number += 1
    runs = []
    for source in sources:
        snap = {**snapshot, "id": source + "-snapshot", "source_id": source}
        store.put(
            "sources",
            source,
            {
                "id": source,
                "portal": "https://data.gov.au/data",
                "metadata": {"title": "Fixture", "license_title": "CC BY"},
            },
        )
        store.put("snapshots", snap["id"], snap)
        run = new_run({"id": source, "slug": source}, snap)
        spec.ontology_hash = run["ontology_hash"]
        mapping = {
            "id": source + "-mapping",
            "config": spec.model_dump(),
            "config_hash": content_hash(spec),
            "version": 1,
        }
        store.put("mappings", mapping["id"], mapping, run["id"])
        approval = {
            "id": source + "-approval",
            "decision": "approved",
            "config_hash": content_hash(spec),
            "reviewer": "TEST FIXTURE; NOT HUMAN EVALUATION",
        }
        store.put("approvals", approval["id"], approval)
        rows = [
            record(source, "csv", i + 20, {"name": f"Synthetic Entity {i}", "abn": abn})
            for i, abn in enumerate(ids)
        ]
        run.update(
            status="completed",
            mapping_id=mapping["id"],
            approval_id=approval["id"],
            partitions_artifact=store.json_blob({"partitions": partition(rows)}),
        )
        store.put("runs", run["id"], run)
        runs.append(run["id"])
    return runs


def test_assembly_writes_typed_rows_and_repeats_exactly(spec, snapshot):
    runs = assembled(spec, snapshot)
    first = assemble(runs)
    assert first["counts"] == {
        "observations": 200,
        "links": 50,
        "unlinked": 0,
        "profiles": 50,
    }
    for table in (identity.membership, identity.link, identity.profile):
        # Every row knows its batch, because the batch is written with them.
        assert count(table, table.c.batch_id == first["id"]) == count(table) > 0
    assert count(ops.batch, ops.batch.c.kind == "pipeline") == 1
    for name in store.TYPED:
        with store.engine().connect() as connection:
            assert connection.execute(select(store.TABLES[name])).all() == []

    by_entity = lambda profiles: sorted(
        profiles, key=lambda p: p["canonical_entity_key"]
    )
    assert same(
        by_entity(store.listing("profiles", owner=first["id"])),
        by_entity(store.read_json(first["result_artifact"])["profiles"]),
    )
    with store.engine().connect() as connection:
        fields = connection.execute(
            select(identity.profile_field).order_by(
                identity.profile_field.c.profile_id, identity.profile_field.c.position
            )
        ).all()
        claim = connection.execute(
            text(
                "SELECT c.name, o.value FROM identity.profile_field f "
                "JOIN evidence.observation o ON (o.source_id, o.id) = "
                "(f.observation_source_id, f.observation_id) "
                "JOIN ontology.concept c ON c.id = f.concept_id "
                "WHERE f.concept_name = 'entity.abn' LIMIT 1"
            )
        ).one()
        identifiers = connection.execute(
            text("SELECT scheme, count(*) FROM identity.entity_identifier GROUP BY 1")
        ).all()
    assert len(fields) == 100 and all(f.observation_id for f in fields)
    assert claim.name == "entity.abn" and valid_abn(claim.value)
    assert [tuple(row) for row in identifiers] == [("entity.abn", 50)]

    # The same inputs again: a new batch with identical versions, no new evidence.
    before = (count(evidence.observation), count(identity.entity))
    second = assemble(runs)
    versions = lambda batch: {
        p["canonical_entity_key"]: p["profile_version"]
        for p in store.listing("profiles", owner=batch["id"])
    }
    assert second["id"] != first["id"] and versions(second) == versions(first)
    assert (count(evidence.observation), count(identity.entity)) == before
    assert count(identity.profile) == 100


def test_a_batch_is_written_with_what_it_owns_or_not_at_all(spec, snapshot):
    snap, *_ = chain(spec, snapshot)
    observation = claims(spec, snap, rows=1)[0]
    store.put_observations([observation])
    reference = [observation["source_id"], observation["source_record_id"]]
    membership = {"batch_id": "batch-1", "record": reference, "entity_id": "entity-1"}
    records = [
        (
            "batches",
            "batch-1",
            {"id": "batch-1", "run_ids": ["run-1"]},
            "",
            "pipeline",
            True,
        ),
        ("memberships", "m-1", membership, "batch-1", "membership", True),
        (
            "links",
            "l-1",
            {"id": "ab" * 32, "source_a_record": reference},
            "batch-1",
            "proposed_link",
            True,
        ),
    ]
    assert store.put_many(records) == 3
    assert store.put_many(records) == 3  # the same batch again writes nothing new
    with store.engine().connect() as connection:
        row = connection.execute(select(identity.membership)).one()
        link = connection.execute(select(identity.link)).one()
    assert (row.batch_id, row.source_id, row.record_id) == ("batch-1", *reference)
    assert (row.extra, link.a_record_id, link.b_record_id) == ({}, reference[1], None)
    assert store.require("memberships", "m-1") == membership

    failing = [
        ("batches", "batch-2", {"id": "batch-2"}, "", "pipeline", True),
        (
            "memberships",
            "m-2",
            {**membership, "batch_id": "batch-2"},
            "batch-2",
            "membership",
            True,
        ),
        (
            "memberships",
            "m-1",
            {**membership, "entity_id": "changed"},
            "batch-1",
            "membership",
            True,
        ),
    ]
    with pytest.raises(ValueError, match="Immutable memberships/m-1"):
        store.put_many(failing)
    assert (
        store.get("batches", "batch-2") is None
        and store.get("memberships", "m-2") is None
    )
    # A second membership of the same record in the same batch is refused.
    with pytest.raises(DBAPIError, match="duplicate key"):
        store.put("memberships", "m-3", membership, "batch-1", "membership")


def test_profiles_keep_their_fields_as_rows_and_read_back_exactly(spec, snapshot):
    snap, *_ = chain(spec, snapshot)
    observation = claims(spec, snap, rows=1)[0]
    store.put_observations([observation])
    cited = {
        "id": observation["id"],
        "source_id": observation["source_id"],
        "source_record_id": observation["source_record_id"],
        "value": observation["value"],
    }
    field = {
        "status": "selected",
        "value": observation["value"],
        "provenance": [cited],
        "alternatives": [],
    }
    profile = {
        "canonical_entity_key": "entity-1",
        "profile_version": "cd" * 32,
        "policy_version": "policy-1",
        "status": "profile_from_proposed_links",
        "uncertainties": ["Scores are uncalibrated."],
        "fields": {
            "zeta.last_in_name_order": {
                "status": "multiple_values",
                "values": ["a", "b"],
            },
            observation["field"]: field,
        },
        "addresses": [{"role": "business", "fields": {"address.state": field}}],
        "groups": [{"id": "g", "scope": "contact", "fields": {}}],
        "source_records": [[observation["source_id"], observation["source_record_id"]]],
    }
    store.put("batches", "batch-1", {"id": "batch-1"}, kind="pipeline")
    store.put(
        "profiles", "batch-1:entity-1", profile, "batch-1", "profile", immutable=True
    )
    stored = store.require("profiles", "batch-1:entity-1")
    assert same(stored, profile) and list(stored["fields"]) == list(profile["fields"])
    with store.engine().connect() as connection:
        row = connection.execute(select(identity.profile)).one()
        fields = connection.execute(
            select(identity.profile_field).order_by(identity.profile_field.c.position)
        ).all()
        address = connection.execute(select(identity.profile_address)).one()
    assert (row.batch_id, row.entity_key, row.profile_version) == (
        "batch-1",
        "entity-1",
        "cd" * 32,
    )
    assert set(row.extra) == {"groups", "source_records"}
    assert [(f.concept_name, f.status, f.value, f.observation_id) for f in fields] == [
        ("zeta.last_in_name_order", "multiple_values", None, None),
        (observation["field"], "selected", observation["value"], observation["id"]),
    ]
    assert fields[1].concept_id is not None
    assert (address.role, address.source_id, address.record_id) == (
        "business",
        observation["source_id"],
        observation["source_record_id"],
    )
    # A record that is not shaped like a profile is kept as it is, without rows.
    odd = {"fields": ["not", "a", "mapping"], "addresses": "none"}
    store.put("profiles", "odd", odd)
    assert store.require("profiles", "odd") == odd
    assert count(identity.profile_field) == 2
    with store.engine().connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(text("UPDATE identity.profile_field SET status = 'x'"))


def test_batches_cache_and_triage_share_a_name_but_not_a_table():
    artifact = store.blob(b"{}")
    store.put("batches", "batch-1", {"id": "batch-1", "run_ids": []}, kind="pipeline")
    store.put("batches", "discovery", {"shortlist": []}, kind="discovery")
    cache = {"id": "enhance-cache-1", "response_artifact": artifact}
    store.put(
        "batches", "enhance-cache-1", cache, kind="enhancement_cache", immutable=True
    )
    store.put("batches", "enhance-cache-2", cache)  # no kind: the key decides
    decision = {
        "id": "triage-1",
        "dataset_id": "d1",
        "probability": 0.91,
        "response_artifact": artifact,
    }
    store.put(
        "batches",
        "triage-1",
        decision,
        "discovery-1",
        "triage_decision",
        immutable=True,
    )
    store.put(
        "ontology_events",
        "call-1",
        {"artifact_id": artifact},
        "job-1",
        "model_cache",
        immutable=True,
    )

    assert (count(ops.batch), count(ops.triage_decision), count(ops.model_cache)) == (
        2,
        1,
        3,
    )
    assert store.get("batches", "enhance-cache-1") == cache
    assert store.get("batches", "triage-1") == decision
    assert store.get("batches", "enhance-cache-missing") is None
    assert store.get("ontology_events", "call-1") == {"artifact_id": artifact}
    assert store.listing("batches", kind="pipeline") == [
        {"id": "batch-1", "run_ids": []}
    ]
    assert store.listing("batches", owner="discovery-1", kind="triage_decision") == [
        decision
    ]
    assert (
        len(store.listing("batches")) == 5
    )  # the ontology job's cache was never a batch
    assert store.listing("ontology_events", kind="model_cache") == [
        {"artifact_id": artifact}
    ]
    store.put(
        "batches", "discovery", {"shortlist": [1]}, kind="discovery"
    )  # a pointer moves
    assert store.require("batches", "discovery") == {"shortlist": [1]}
    with pytest.raises(ValueError, match="append-only"):
        store.put(
            "batches",
            "enhance-cache-1",
            {"id": "enhance-cache-1", "response_artifact": None},
        )
    with store.engine().connect() as connection:
        assert (
            connection.execute(select(ops.triage_decision.c.probability)).scalar_one()
            == 0.91
        )
        assert (
            connection.execute(
                select(ops.model_cache.c.response_artifact).where(
                    ops.model_cache.c.id == "enhance-cache-1"
                )
            ).scalar_one()
            == artifact
        )


def test_a_model_call_is_settled_once_and_never_changes_again(monkeypatch):
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "10")
    key = budget.reserve("experiment", "run-1", "onboarding", "gpt-6-luna", 1000, 100)
    reserved = store.require("budget_reservations", key)
    assert reserved["status"] == "reserved"
    budget.settle(key)  # usage unknown: the reservation stands
    assert store.require("budget_reservations", key)["status"] == "reserved"
    budget.settle(key, 1000, 100)
    settled = store.require("budget_reservations", key)
    assert settled["status"] == "settled" and settled["input_tokens"] == 1000
    with store.engine().connect() as connection:
        row = connection.execute(select(ops.model_call)).one()
    assert (row.experiment_id, row.caller_id, row.stage, row.status) == (
        "experiment",
        "run-1",
        "onboarding",
        "settled",
    )
    assert row.charge_usd == settled["charge_usd"] and row.input_tokens == 1000
    budget.settle(key, 1000, 100)  # the same settlement again is accepted
    with pytest.raises(DBAPIError, match="can no longer change"):
        budget.settle(key, 5000, 100)
    assert store.require("budget_reservations", key) == settled
    assert budget.summary("experiment")["attempts"] == 1


def test_events_and_labels_stay_separately_countable():
    opened = store.event(
        "run-1", "enhancement_usage", {"status": "pending", "budget_charge_usd": 0.5}
    )
    store.put(
        "events",
        opened["id"],
        {**opened, "status": "success", "budget_charge_usd": 0.25},
        "run-1",
        "enhancement_usage",
    )
    store.event("run-1", "enhancement_usage", {"budget_charge_usd": 1})
    store.event("run-2", "enhancement_usage", {"budget_charge_usd": 4.0})
    assert store.charged("run-1", "enhancement_usage") == 1.25
    assert store.listing("events", owner="run-1")[0]["status"] == "success"
    with store.engine().connect() as connection:
        assert connection.execute(
            select(ops.event.c.at).where(ops.event.c.id == opened["id"])
        ).scalar_one() == datetime.fromisoformat(opened["at"])

    for kind, reviewer in (
        ("human_label", "owner"),
        ("ai_label", "model"),
        ("ai_label", "model"),
    ):
        number = count(ops.evaluation)
        label = {
            "worksheet_id": "sheet",
            "item_id": str(number),
            "verdict": "correct",
            "reviewer": reviewer,
        }
        store.put("evaluations", f"label-{number}", label, "sheet", kind)
    store.put(
        "evaluations",
        "label-0",
        {"worksheet_id": "sheet", "item_id": "0", "verdict": "incorrect"},
        "sheet",
        "human_label",
    )
    assert [
        v["verdict"]
        for v in store.listing("evaluations", owner="sheet", kind="human_label")
    ] == ["incorrect"]
    with store.engine().connect() as connection:
        kinds = dict(
            connection.execute(
                text("SELECT kind, count(*) FROM ops.evaluation GROUP BY 1")
            ).all()
        )
    assert kinds == {"human_label": 1, "ai_label": 2}


def test_embeddings_are_kept_once_for_similarity_search():
    near, far = [1.0] + [0.0] * 1535, [0.0] * 1535 + [1.0]
    assert store.put_embedding("near", "model", near)
    assert store.put_embedding("far", "model", far)
    assert store.put_embedding("near", "other-model", far)  # the first one is kept
    assert not store.put_embedding("short", "model", [1.0, 0.0])  # not the indexed size
    with store.engine().connect() as connection:
        ranked = connection.execute(
            text(
                "SELECT key, model FROM ops.embedding "
                "ORDER BY embedding <=> CAST(:probe AS vector) LIMIT 2"
            ),
            {"probe": "[" + ",".join(["0.9"] + ["0.1"] + ["0"] * 1534) + "]"},
        ).all()
        index = connection.execute(
            text(
                "SELECT indexdef FROM pg_indexes WHERE tablename = 'embedding' AND indexdef LIKE '%hnsw%'"
            )
        ).scalar_one()
    assert [tuple(row) for row in ranked] == [("near", "model"), ("far", "model")]
    assert "vector_cosine_ops" in index


def test_backfill_copies_identity_and_operations_and_is_idempotent(
    spec, snapshot, clear_store, tmp_path
):
    runs = assembled(spec, snapshot)
    batch = assemble(runs)
    key = budget.reserve("experiment", runs[0], "onboarding", "gpt-6-luna", 10, 10)
    budget.settle(key, 10, 10)
    store.event(runs[0], "model_usage", {"status": "success"})
    store.put(
        "evaluations",
        "sheet",
        {"id": "sheet", "batch_id": batch["id"], "items": []},
        batch["id"],
        "worksheet",
    )
    artifact = store.blob(b"{}")
    store.put(
        "batches",
        "enhance-cache-1",
        {"id": "enhance-cache-1", "response_artifact": artifact},
        kind="enhancement_cache",
    )
    store.put(
        "ontology_events", "call-1", {"artifact_id": artifact}, "job", "model_cache"
    )
    moved = {name: list(store.records(name)) for name in LEGACY_NAMES}
    moved["ontology_events"] = list(
        store.records("ontology_events", kind="model_cache")
    )
    assert all(moved.values())

    # Keep the evidence spine; move identity and operations back to legacy rows.
    stamp = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
    with store.engine().begin() as connection:
        connection.execute(
            text(
                "TRUNCATE identity.entity, identity.membership, identity.link, identity.profile, "
                "identity.profile_field, identity.profile_address, ops.batch, ops.triage_decision, "
                "ops.model_cache, ops.model_call, ops.event, ops.evaluation CASCADE"
            )
        )
        for position, (name, rows) in enumerate(moved.items()):
            connection.execute(
                insert(store.TABLES[name]),
                [{**row, "created_at": stamp.replace(second=position)} for row in rows],
            )
    spec_ = importlib.util.spec_from_file_location(
        "migration_baseline", Path("scripts/migration_baseline.py")
    )
    script = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(script)
    url = store.engine().url.render_as_string(hide_password=False)
    saved = tmp_path / "baseline.json"
    # The baseline describes the legacy tables, so they hold the spine as well.
    from link_lens.db import ontology as registry

    spine = (
        "sources",
        "snapshots",
        "runs",
        "mappings",
        "approvals",
        "artifacts",
        "observations",
    )
    with store.engine().begin() as connection:
        for name in spine:
            connection.execute(
                insert(store.TABLES[name]),
                [{**row, "created_at": stamp} for row in store.records(name)],
            )
        connection.execute(
            insert(store.TABLES["ontologies"]),
            [
                {
                    "id": key,
                    "owner_id": "",
                    "kind": "ontology",
                    "payload": {"id": key},
                    "created_at": stamp,
                }
                for key in registry.version_hashes(connection)
            ],
        )
    assert script.main(["--database-url", url, "--output", str(saved)]) == 0
    check = ["--database-url", url, "--typed", "--check", str(saved)]

    first = backfill.identity_and_operations()
    assert first["profiles"]["copied"] == 50 and first["memberships"]["copied"] == 100
    assert first["batches"]["copied"] == 1 and first["model_cache"]["copied"] == 2
    assert (
        first["profile_fields_citing_an_observation"] == first["profile_fields"] == 100
    )
    assert all(
        value["not_in_typed_column"] == {}
        for value in first.values()
        if isinstance(value, dict)
    )
    second = backfill.identity_and_operations()
    assert all(
        value["copied"] == 0 for value in second.values() if isinstance(value, dict)
    )
    assert script.main(check) == 0
    for name in LEGACY_NAMES:
        assert same(
            sorted(store.records(name), key=lambda r: r["id"]),
            sorted(moved[name], key=lambda r: r["id"]),
        ), name
    assert count(identity.profile, identity.profile.c.batch_id == batch["id"]) == 50
    with store.engine().connect() as connection:
        assert connection.execute(
            select(ops.batch.c.created_at)
        ).scalar_one() == stamp.replace(second=0)
    report = script.baseline(url, typed=True)
    assert report["batches"][batch["id"]]["profile_versions"]["count"] == 50
    assert report["experiments"]["experiment"]["budget_reservations"] == 1


def test_restored_rows_find_their_batch(spec, snapshot, clear_store, tmp_path):
    from link_lens.frozen import freeze, thaw

    batch = assemble(assembled(spec, snapshot))
    before = {name: list(store.records(name)) for name in LEGACY_NAMES}
    path = tmp_path / "evidence.zip"
    freeze(path)
    clear_store()
    thaw(path)
    for name in LEGACY_NAMES:
        assert same(
            sorted(store.records(name), key=lambda r: r["id"]),
            sorted(before[name], key=lambda r: r["id"]),
        ), name
    for table in (identity.membership, identity.link, identity.profile):
        assert count(table, table.c.batch_id == batch["id"]) == count(table) > 0
    assert count(identity.profile_field) == 100


def test_commands_log_how_they_ended(monkeypatch, capsys):
    logs.logger.handlers.clear()

    def run(*arguments):
        monkeypatch.setattr(sys, "argv", ["link-lens", *arguments])
        try:
            cli.main()
        except SystemExit as stop:
            code = stop.code
        except Exception as error:  # noqa: BLE001
            code = type(error).__name__
        lines = [l for l in capsys.readouterr().err.splitlines() if l.startswith("{")]
        return code, json.loads(lines[-1])

    code, line = run("source", "state", "--kind", "none")
    assert code == 0
    assert (line["event"], line["command"], line["exit_code"], line["level"]) == (
        "command.finished",
        "source state",
        0,
        "info",
    )
    assert isinstance(line["seconds"], float) and line["at"].endswith("+00:00")
    code, line = run("source", "state", "--no-such-option")
    assert code == 2 and (line["exit_code"], line["level"]) == (2, "warning")
    code, line = run("ontology", "show", "not-a-hash")
    assert code == "KeyError"
    assert (line["event"], line["error_type"], line["exit_code"]) == (
        "command.failed",
        "KeyError",
        1,
    )

    class Leaky(Exception):
        pass

    assert logs.error_fields(Leaky("api key sk-123")) == {"error_type": "Leaky"}
    assert logs.error_fields(ValueError("plain"))["error"] == "plain"
    logs.logger.handlers.clear()
