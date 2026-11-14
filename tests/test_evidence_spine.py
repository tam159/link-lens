"""Typed catalog, onboarding and evidence tables behind the store facade."""

import hashlib
import importlib.util
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from link_lens import backfill, blobs, ontology, ontology_gate, store
from link_lens.contracts import MappingSpec, content_hash
from link_lens.db import catalog, evidence, onboarding
from link_lens.db.records import same
from link_lens.extraction import extract
from link_lens.readers import record
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError

SOURCE = "source-a"


def count(table):
    with store.engine().connect() as connection:
        return connection.execute(select(func.count()).select_from(table)).scalar_one()


def column(table, name, key):
    with store.engine().connect() as connection:
        return connection.execute(
            select(table.c[name]).where(table.c.id == key)
        ).scalar_one()


def extended_spec(spec):
    """A mapping bound to an ontology version with a group, an integer and a date."""
    parent = ontology.legacy()
    added = [
        ontology.Concept(
            name="financial.period",
            definition="Reporting period stated by the source",
            type="string",
            scope="financial_period",
        ),
        ontology.Concept(
            name="financial.staff",
            definition="Staff count for the reporting period",
            type="integer",
            scope="financial_period",
            requires=["financial.period"],
        ),
    ]
    version = ontology.register(
        {
            "version": "spine-test",
            "parent_hash": ontology.digest(parent),
            "concepts": {
                **deepcopy(parent["concepts"]),
                **{c.name: c.model_dump() for c in added},
            },
        }
    )
    data = spec.model_dump()
    data["ontology_hash"] = version
    for source_field, target in (
        ("period", "financial.period"),
        ("staff", "financial.staff"),
    ):
        data["fields"].append(
            {
                "source_fields": [source_field],
                "canonical_field": target,
                "group": "annual_return",
                "transformations": [{"op": "trim"}],
                "confidence": 0.8,
                "evidence": "Explicit synthetic source column",
            }
        )
    return MappingSpec.model_validate(data)


def chain(spec, snapshot, source=SOURCE, run_id="run-1", kind="registered"):
    """A stored source, snapshot, run, mapping and approval, as onboarding leaves them."""
    blob = store.blob(f"bytes of {source}".encode(), "text/csv", "data.csv")
    store.put(
        "sources",
        source,
        {
            "id": source,
            "slug": "fixture",
            "portal": "https://portal.example",
            "metadata": {
                "title": "Fixture title",
                "organization": {"title": "Publisher"},
            },
        },
        kind=kind,
    )
    snap = {
        **snapshot,
        "id": hashlib.sha256(source.encode()).hexdigest(),
        "source_id": source,
        "artifact_id": blob,
        "sha256": blob,
        "resource_id": "resource-1",
        # Timestamps in the form the downloader writes them.
        "receipt": {**snapshot["receipt"], "retrieved_at": "2025-02-01T00:00:00+00:00"},
        "licence_url": None,
        "documentation": [],
        "dataset_notes": "",
        "inspection": {"format": "csv"},
    }
    store.put("snapshots", snap["id"], snap, source, "snapshot", immutable=True)
    run = {
        "id": run_id,
        "experiment_id": "experiment",
        "source_id": source,
        "source_slug": "fixture",
        "snapshot_id": snap["id"],
        "status": "completed",
        "model_calls": 3,
        "active_seconds": 1.5,
        "calculated_cost_usd": None,
        "created_at": "2026-01-02T03:04:05.123456+00:00",
        "validation": {"passed": True},
    }
    store.put("runs", run_id, run, source, "onboarding")
    config = spec.model_dump(mode="json")
    mapping = {
        "id": run_id + ":1",
        "run_id": run_id,
        "version": 1,
        "config": config,
        "config_hash": content_hash(config),
        "model": "test-model",
        "status": "proposed",
        "generated_by": "runtime_agent",
        "created_at": "2026-01-02T03:05:00+00:00",
    }
    store.put("mappings", mapping["id"], mapping, run_id, "mapping", immutable=True)
    approval = {
        "id": hashlib.sha256((run_id + "approval").encode()).hexdigest(),
        "run_id": run_id,
        "mapping_id": mapping["id"],
        "config_hash": mapping["config_hash"],
        "decision": "approved",
        "reviewer": "TEST FIXTURE; NOT HUMAN EVALUATION",
        "feedback": "",
        "identity_basis": "fixture",
        "at": "2026-01-02T03:06:00+00:00",
    }
    store.put("approvals", approval["id"], approval, run_id, "approval", immutable=True)
    return snap, run, mapping, approval


def claims(spec, snap, rows=5):
    values = [
        record(
            snap["sha256"],
            "csv",
            n + 2,
            {
                "name": f"Entity {n}",
                "abn": "51824753556",
                "period": "FY25",
                "staff": str(n + 1),
            },
        )
        for n in range(rows)
    ]
    return sorted(extract(spec, values, snap)["observations"], key=lambda o: o["id"])


def test_records_read_back_exactly_whatever_they_hold(spec, snapshot):
    snap, run, mapping, approval = chain(spec, snapshot)
    assert same(store.require("snapshots", snap["id"]), snap)
    assert same(store.require("runs", run["id"]), run)
    assert same(store.require("mappings", mapping["id"]), mapping)
    assert same(store.require("approvals", approval["id"]), approval)
    assert store.listing("mappings", owner=run["id"]) == [mapping]
    assert store.listing("mappings", owner="another-run") == []
    assert store.listing("sources", kind="registered")[0]["slug"] == "fixture"

    # Typed columns hold what fits; the rest stays in the JSON column.
    assert column(onboarding.run, "status", run["id"]) == "completed"
    assert column(onboarding.run, "model_calls", run["id"]) == 3
    assert column(onboarding.run, "started_at", run["id"]) == datetime(
        2026, 1, 2, 3, 4, 5, 123456, tzinfo=UTC
    )
    state = column(onboarding.run, "state", run["id"])
    assert state == {
        "id": run["id"],
        "source_slug": "fixture",
        "calculated_cost_usd": None,
        "validation": {"passed": True},
    }
    assert column(catalog.snapshot, "retrieved_at", snap["id"]) == datetime(
        2025, 2, 1, tzinfo=UTC
    )
    with store.engine().connect() as connection:
        assert connection.execute(
            select(text("title, publisher")).select_from(catalog.source)
        ).one() == ("Fixture title", "Publisher")

    odd = {
        "status": 7,  # not text
        "model_calls": 2.0,  # not an integer
        "active_seconds": 3,  # an integer where a float is usual
        "input_tokens": True,
        "created_at": "yesterday",
        "completed_at": "2026-01-02T03:04:05",  # no offset
        "nested": {"a": [1, 1.0, None]},
    }
    store.put("runs", "odd", odd)
    assert same(store.require("runs", "odd"), odd)
    assert column(onboarding.run, "status", "odd") is None
    assert column(onboarding.run, "active_seconds", "odd") == 3.0
    assert column(onboarding.run, "completed_at", "odd") == datetime(
        2026, 1, 2, 3, 4, 5, tzinfo=UTC
    )
    store.put("runs", "odd", {"status": "changed"}, "owner", "kind")
    assert store.require("runs", "odd") == {"status": "changed"}
    assert store.listing("runs", owner="owner", kind="kind") == [{"status": "changed"}]


def test_reference_columns_hold_only_rows_that_exist(spec, snapshot):
    store.put("runs", "early", {"source_id": "later-source", "snapshot_id": "later"})
    assert column(onboarding.run, "source_id", "early") is None
    assert store.require("runs", "early")["snapshot_id"] == "later"
    store.put("sources", "later-source", {"id": "later-source"})
    store.put("snapshots", "later", {"source_id": "later-source"})
    store.put("runs", "early", {"source_id": "later-source", "snapshot_id": "later"})
    assert column(onboarding.run, "source_id", "early") == "later-source"
    assert column(onboarding.run, "snapshot_id", "early") == "later"
    assert column(onboarding.run, "state", "early") == {}
    with store.engine().connect() as connection:
        assert onboarding.runs.unresolved(connection) == {}
    store.put("runs", "pseudo", {"source_id": "ontology"})
    with store.engine().connect() as connection:
        assert onboarding.runs.unresolved(connection) == {"source_id": 1}


def test_append_only_records_cannot_change(spec, snapshot):
    snap, run, mapping, approval = chain(spec, snapshot)
    store.put("snapshots", snap["id"], snap)  # the same record again is accepted
    with pytest.raises(ValueError, match="Immutable snapshots"):
        store.put("snapshots", snap["id"], {**snap, "licence": "other"}, immutable=True)
    for table, key, record_ in (
        ("snapshots", snap["id"], snap),
        ("mappings", mapping["id"], mapping),
        ("approvals", approval["id"], approval),
    ):
        with pytest.raises(ValueError, match="append-only"):
            store.put(table, key, {**record_, "changed": True})
        assert same(store.require(table, key), record_)
    store.put_observations(claims(spec, snap))
    for statement in (
        "UPDATE catalog.snapshot SET licence = 'x'",
        "UPDATE catalog.artifact SET name = 'x'",
        "UPDATE onboarding.mapping_config SET subject_role = 'x'",
        "UPDATE onboarding.mapping SET status = 'x'",
        "UPDATE onboarding.approval SET decision = 'x'",
        "UPDATE evidence.source_record SET sheet = 'x'",
        "UPDATE evidence.observation SET value = 'x'",
    ):
        with store.engine().connect() as connection:
            with pytest.raises(DBAPIError, match="append-only"):
                connection.execute(text(statement))


def test_a_config_is_stored_once_and_indexed_by_concept(spec, snapshot):
    _, _, first, _ = chain(spec, snapshot)
    _, _, second, _ = chain(spec, snapshot, source="source-b", run_id="run-2")
    assert first["config_hash"] == second["config_hash"]
    assert count(onboarding.mapping) == 2 and count(onboarding.mapping_config) == 1
    with store.engine().connect() as connection:
        fields = connection.execute(
            text(
                "SELECT c.name, f.source_fields FROM onboarding.mapping_field f "
                "JOIN ontology.concept c ON c.id = f.concept_id ORDER BY f.position"
            )
        ).all()
        roles = connection.execute(select(onboarding.mapping_config)).one()
    assert [tuple(f) for f in fields] == [
        ("entity.legal_name", ["name"]),
        ("entity.abn", ["abn"]),
    ]
    assert (roles.subject_role, roles.source_kind, roles.source_reliability) == (
        "legal_entity",
        "company_register",
        0.9,
    )
    # A config that does not hash to its config_hash is kept, but not as a config.
    wrong = {"config": {"fields": []}, "config_hash": "ab" * 32}
    store.put("mappings", "wrong", wrong)
    assert store.require("mappings", "wrong") == wrong
    assert column(onboarding.mapping, "config_hash", "wrong") is None
    assert count(onboarding.mapping_config) == 1


def test_observations_are_stored_once_and_read_back_exactly(spec, snapshot):
    spec = extended_spec(spec)
    snap, *_ = chain(spec, snapshot)
    observations = claims(spec, snap)
    assert {o["field"] for o in observations} == {
        "entity.legal_name",
        "entity.abn",
        "financial.period",
        "financial.staff",
    }
    assert store.put_observations(observations) == 20
    assert store.put_observations(observations) == 0  # an identical load adds nothing
    assert store.put_observations(observations[:3] + claims(spec, snap, rows=6)) == 4

    stored = store.listing("observations")
    assert len(stored) == 24
    for original in observations:
        assert same(store.require("observations", original["id"]), original)
    staff = next(o for o in stored if o["field"] == "financial.staff")
    assert isinstance(staff["value"], int) and staff["group_name"] == "annual_return"
    assert count(evidence.source_record) == 6
    with store.engine().connect() as connection:
        rows = connection.execute(select(evidence.observation)).all()
        record_ = connection.execute(select(evidence.source_record)).first()
    assert all(row.extra == {} for row in rows)  # everything is in columns or derived
    assert {row.timestamp_basis for row in rows} == {"snapshot"}
    assert {row.engine for row in rows} == {"extractor-1"}
    assert (record_.snapshot_id, record_.sheet) == (snap["id"], "csv")
    assert store.get("observations", "ab" * 32) is None
    with pytest.raises(ValueError, match="by owner"):
        store.listing("observations", owner="run-1")


def test_an_observation_that_differs_from_what_is_derived_stays_exact(spec, snapshot):
    snap, *_ = chain(spec, snapshot)
    unusual = claims(spec, snap, rows=1)[0]
    unusual.update(
        licence="A licence the snapshot does not state",
        observed_at="2024-05-06T07:08:09+10:00",
        observed_at_basis="source record statement field",
        timezone_assumption=None,
        confidence={"source_reliability": 0.9, "field_confidence": 1},
        note="an extra key",
    )
    unusual["id"] = content_hash({k: v for k, v in unusual.items() if k != "id"})
    assert store.put_observations([unusual]) == 1
    assert same(store.require("observations", unusual["id"]), unusual)
    with store.engine().connect() as connection:
        row = connection.execute(select(evidence.observation)).one()
    assert row.timestamp_basis == "record" and row.timezone_assumed is False
    assert row.observed_at == datetime(2024, 5, 5, 21, 8, 9, tzinfo=UTC)
    assert set(row.extra) == {"licence", "observed_at", "confidence", "note"}


def test_an_observation_needs_its_snapshot_config_and_concept(spec, snapshot):
    snap, *_ = chain(spec, snapshot)
    good = claims(spec, snap, rows=1)[0]
    for change, message in (
        ({"config_hash": "cd" * 32}, "mapping config is not stored"),
        ({"snapshot_id": "missing"}, "snapshot is not stored"),
        ({"field": "invented.concept"}, "not in the mapping's ontology"),
        ({"id": "not-a-hash"}, "not a SHA-256 digest"),
        ({"observed_at": "not a time"}, "missing or malformed"),
    ):
        with pytest.raises(ValueError, match=message):
            store.put_observations([{**good, **change}])
    incomplete = {k: v for k, v in good.items() if k != "licence"}
    with pytest.raises(ValueError, match="lacks licence"):
        store.put_observations([incomplete])
    assert count(evidence.observation) == 0 and count(evidence.source_record) == 0


def partitions():
    with store.engine().connect() as connection:
        return set(
            connection.execute(
                text(
                    "SELECT o.tableoid::regclass::text FROM evidence.observation o "
                    "UNION SELECT r.tableoid::regclass::text FROM evidence.source_record r"
                )
            ).scalars()
        )


def test_a_registered_source_gets_its_own_partitions(spec, snapshot):
    snap, *_ = chain(spec, snapshot, source="registered-source")
    store.put_observations(claims(spec, snap))
    suffix = hashlib.md5(b"registered-source").hexdigest()[:16]
    assert partitions() == {
        f"evidence.observation_{suffix}",
        f"evidence.source_record_{suffix}",
    }
    other, *_ = chain(
        spec, snapshot, source="catalogue-source", run_id="run-2", kind=""
    )
    store.put_observations(claims(spec, other))
    assert "evidence.observation_default" in partitions()
    # Rows already in the default partition stay there; asking again is harmless.
    with store.engine().begin() as connection:
        connection.execute(
            text("SELECT evidence.ensure_source_partitions('catalogue-source')")
        )
    assert len(partitions()) == 4 and count(evidence.observation) == 20


def test_pipeline_role_writes_evidence_and_product_role_reads_none(spec, snapshot):
    snap, *_ = chain(spec, snapshot)
    observations = claims(spec, snap)
    with store.engine().begin() as connection:
        connection.execute(text("SET LOCAL ROLE linklens_pipeline"))
        assert (
            evidence.insert_observations(connection, observations, store._root_hash())
            == 10
        )
        connection.execute(
            text("SELECT evidence.ensure_source_partitions('new-source')")
        )
        assert (
            connection.execute(text("SELECT count(*) FROM onboarding.run")).scalar_one()
            == 1
        )
    for role, statement in (
        ("linklens_pipeline", "DELETE FROM evidence.observation"),
        ("linklens_product", "SELECT * FROM evidence.observation"),
        ("linklens_product", "SELECT * FROM catalog.source"),
        ("linklens_product", "SELECT evidence.ensure_source_partitions('x')"),
    ):
        with store.engine().connect() as connection:
            connection.execute(text(f"SET LOCAL ROLE {role}"))
            with pytest.raises(DBAPIError, match="permission denied"):
                connection.execute(text(statement))


class FakeS3:
    def __init__(self):
        self.objects, self.puts = {}, 0

    def put_object(self, Bucket, Key, Body):
        self.puts += 1
        self.objects[Bucket, Key] = Body

    def get_object(self, Bucket, Key):
        import io

        return {"Body": io.BytesIO(self.objects[Bucket, Key])}


def test_artifacts_can_live_in_an_s3_compatible_store(tmp_path, monkeypatch):
    local_key = store.blob(b"kept locally", "text/plain", "local.txt")
    assert store.blob_path(local_key).read_bytes() == b"kept locally"
    assert column_uri(local_key) == f"local:blobs/{local_key[:2]}/{local_key}"

    client = FakeS3()
    remote = blobs.S3BlobStore("bucket", "prefix/", tmp_path / "cache", client=client)
    local = blobs.stores()["local"]
    monkeypatch.setattr(blobs, "stores", lambda: {"s3": remote, "local": local})
    key = store.blob(b"kept remotely", "text/plain", "remote.txt")
    assert column_uri(key) == f"s3://bucket/prefix/blobs/{key[:2]}/{key}"
    assert store.blob(b"kept remotely", "text/plain", "again.txt") == key
    assert client.puts == 1  # registered content is not uploaded again
    assert store.blob_path(key).read_bytes() == b"kept remotely"
    assert store.blob_path(key).parent.parent.parent == tmp_path / "cache"
    assert store.require("artifacts", key) == {
        "id": key,
        "sha256": key,
        "size": 13,
        "media_type": "text/plain",
        "name": "remote.txt",
    }
    # Artifacts registered locally stay readable while new ones go to the bucket.
    assert store.blob_path(local_key).read_bytes() == b"kept locally"

    client.objects[next(iter(client.objects))] = b"tampered"
    (tmp_path / "cache" / "blobs" / key[:2] / key).unlink()
    with pytest.raises(ValueError, match="does not match its hash"):
        store.blob_path(key)
    with pytest.raises(KeyError):
        store.blob_path("ef" * 32)


def column_uri(key):
    with store.engine().connect() as connection:
        return catalog.artifact_uri(connection, key)


def legacy_rows(table):
    with store.engine().connect() as connection:
        return connection.execute(select(store.TABLES[table])).all()


def make_legacy(spec, snapshot):
    """Build records through the store, move them to the generic tables, clear typed."""
    spec = extended_spec(spec)
    snap, run, mapping, approval = chain(spec, snapshot)
    store.put(
        "runs",
        "ontology-job",
        {"id": "ontology-job", "source_id": "ontology"},
        "ontology",
        "ontology",
    )
    observations = claims(spec, snap)
    store.put_observations(observations)
    moved = {
        name: list(store.records(name))
        for name in (
            "artifacts",
            "sources",
            "snapshots",
            "runs",
            "mappings",
            "approvals",
        )
    }
    moved["observations"] = [
        {"id": o["id"], "owner_id": run["id"], "kind": "observation", "payload": o}
        for o in observations
    ]
    return moved, observations


def test_backfill_copies_every_record_and_is_idempotent(
    spec, snapshot, clear_store, tmp_path
):
    moved, observations = make_legacy(spec, snapshot)
    versions = ontology.resolve(extended_spec(spec).ontology_hash)
    clear_store()
    ontology.register(versions)
    # The generic store also listed each ontology version, as phase 1 left it.
    moved["ontologies"] = [
        {"id": key, "owner_id": "", "kind": "ontology", "payload": {"id": key}}
        for key in (ontology.digest(ontology.legacy()), ontology.digest(versions))
    ]
    stamp = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
    with store.engine().begin() as connection:
        for name, rows in moved.items():
            connection.execute(
                insert(store.TABLES[name]),
                [{**row, "created_at": stamp} for row in rows],
            )
    spec_ = importlib.util.spec_from_file_location(
        "migration_baseline", Path("scripts/migration_baseline.py")
    )
    script = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(script)
    url = store.engine().url.render_as_string(hide_password=False)
    saved = tmp_path / "baseline.json"
    assert script.main(["--database-url", url, "--output", str(saved)]) == 0
    check = ["--database-url", url, "--typed", "--check", str(saved)]
    assert script.main(check) == 1  # nothing is typed yet

    first = backfill.evidence_spine(chunk=7)
    assert first["observations"] == {
        "legacy": 20,
        "copied": 20,
        "typed": 20,
        "kept_outside_columns": 0,
        "keys_kept_outside_columns": {},
    }
    assert first["runs"] == {
        "legacy": 2,
        "copied": 2,
        "typed": 2,
        "not_in_typed_column": {"source_id": 1},
    }
    assert (
        first["mapping_configs"],
        first["mapping_fields"],
        first["source_records"],
    ) == (1, 4, 5)
    second = backfill.evidence_spine(chunk=7)
    assert all(
        value["copied"] == 0 for value in second.values() if isinstance(value, dict)
    )
    assert script.main(check) == 0

    del moved["ontologies"]
    for name, rows in moved.items():
        assert list(store.records(name)) == sorted(rows, key=lambda r: r["id"]) or same(
            sorted(store.records(name), key=lambda r: r["id"]),
            [
                {**row, "owner_id": "" if name == "observations" else row["owner_id"]}
                for row in sorted(rows, key=lambda r: r["id"])
            ],
        )
        assert len(legacy_rows(name)) == len(rows)  # copied, never moved
    assert column(catalog.source, "created_at", SOURCE) == stamp
    # A typed record that the baseline does not know is reported.
    snap = store.listing("snapshots")[0]
    store.put_observations(claims(extended_spec(spec), snap, rows=6))
    assert script.main(check) == 1


def test_onboarding_and_extraction_write_only_typed_tables(monkeypatch, spec, snapshot):
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    from link_lens import agent
    from link_lens.contracts import SemanticReview
    from link_lens.ingestion import new_run

    data = (
        "name,abn\n" + "".join(f"Example {i},51824753556\n" for i in range(60))
    ).encode()
    blob = store.blob(data)
    snapshot.update(
        artifact_id=blob,
        sha256=blob,
        inspection={"format": "csv", "preview": [["name", "abn"]]},
        dataset_notes="",
        documentation=[],
    )
    snapshot["receipt"]["partial"] = False
    source = {"id": SOURCE, "slug": "fixture", "metadata": {"title": "Test fixture"}}
    store.put("sources", SOURCE, source, kind="registered")
    store.put("snapshots", snapshot["id"], snapshot, SOURCE, "snapshot", immutable=True)
    run = new_run(source, snapshot)

    def fake_call(run_id, schema, prompt, stage):
        if stage == "inspect":
            return agent.AnalysisPlan(
                reader=spec.reader, grain_hypothesis=spec.record_grain, uncertainties=[]
            )
        if stage == "propose_mapping":
            return spec
        return SemanticReview(
            acceptable=True,
            blocking_issues=[],
            warnings=[],
            evidence_checked=["fixture"],
        )

    monkeypatch.setattr(agent, "call", fake_call)
    graph = agent.build_graph(InMemorySaver())
    config = {"configurable": {"thread_id": "typed-only"}}
    graph.invoke({"run_id": run["id"]}, config)
    digest = store.require("mappings", store.require("runs", run["id"])["mapping_id"])[
        "config_hash"
    ]
    graph.invoke(
        Command(resume=[{"type": "accept", "args": {"config_hash": digest}}]), config
    )
    assert store.require("runs", run["id"])["status"] == "completed"

    typed = {
        table: count(table)
        for table in (
            catalog.artifact,
            catalog.source,
            catalog.snapshot,
            onboarding.run,
            onboarding.mapping,
            onboarding.approval,
            evidence.source_record,
            evidence.observation,
        )
    }
    assert all(typed.values()), typed
    for name in store.TYPED:
        assert legacy_rows(name) == []
    assert column(onboarding.run, "snapshot_id", run["id"]) == snapshot["id"]
    assert (
        column(onboarding.approval, "config_hash", store.listing("approvals")[0]["id"])
        == digest
    )

    # The same extraction again inserts nothing.
    agent.extract_node({"run_id": run["id"]})
    assert count(evidence.observation) == typed[evidence.observation]
    assert count(evidence.source_record) == typed[evidence.source_record]
    assert count(onboarding.approval) == 1


def test_archive_restores_typed_records_exactly(spec, snapshot, clear_store, tmp_path):
    from link_lens.frozen import freeze, thaw

    spec = extended_spec(spec)
    snap, *_ = chain(spec, snapshot)
    store.put_observations(claims(spec, snap))
    before = {name: list(store.records(name)) for name in store.TABLES}
    path = tmp_path / "evidence.zip"
    freeze(path)
    assert thaw(path)["restored"] == sum(len(rows) for rows in before.values())
    clear_store()
    assert store.listing("observations") == []
    thaw(path)
    after = {name: list(store.records(name)) for name in store.TABLES}
    for name in before:
        assert same(
            sorted(after[name], key=lambda r: r["id"]),
            sorted(before[name], key=lambda r: r["id"]),
        ), name
    assert len(after["observations"]) == 20 and count(evidence.source_record) == 5


def test_gate_validates_stored_observations_and_reports_impact(
    spec, snapshot, monkeypatch
):
    pytest.importorskip("linkml")
    pytest.importorskip("pyshacl")
    spec = extended_spec(spec)
    snap, *_ = chain(spec, snapshot)
    observations = claims(spec, snap)
    store.put_observations(observations)
    version = spec.ontology_hash
    report = {c["check"]: c for c in ontology_gate.run(version)["checks"]}
    assert report["shacl_observations"]["result"] == "pass"
    assert report["shacl_observations"]["detail"]["sampled"] == 20
    impact = report["impact"]["detail"]
    assert report["impact"]["result"] == "pass"
    assert impact["by_concept"] == {
        "financial.period": {"mapping_configs": 1, "observations": 5},
        "financial.staff": {"mapping_configs": 1, "observations": 5},
    }

    # A stored value the ontology does not allow fails the check and is named.
    bad = {
        **next(o for o in observations if o["field"] == "financial.staff"),
        "value": "many",
    }
    bad["id"] = content_hash({k: v for k, v in bad.items() if k != "id"})
    store.put_observations([bad])
    failed = {c["check"]: c for c in ontology_gate.run(version)["checks"]}[
        "shacl_observations"
    ]
    assert failed["result"] == "fail"
    assert [v["observation"] for v in failed["detail"]["violations"]] == [bad["id"]]
    with pytest.raises(ValueError, match="shacl_observations"):
        ontology.activate(version, "experiment", "reviewer")

    assert json.dumps(report["impact"]["detail"])  # the detail is plain JSON
