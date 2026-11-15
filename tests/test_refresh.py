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


def two_sources(spec):
    """Two registered sources that state the same three ABNs, each with an approved mapping."""
    built = {}
    for source_id, prefix in (("source-a", "Alpha"), ("source-b", "Beta")):
        store.put(
            "sources",
            source_id,
            {
                "id": source_id,
                "slug": source_id,
                "portal": "https://data.gov.au/data",
                "metadata": {"title": source_id, "license_title": "CC BY"},
            },
            kind="registered",
        )
        rows = [[f"{prefix} Entity {n}", abn] for n, abn in enumerate(ABNS)]
        snapshot = snapshot_of(
            source_id, csv_of(["name", "abn"], rows), "2025-02-01T00:00:00Z"
        )
        run, _ = approve(spec, source_id, snapshot)
        built[source_id] = {"snapshot": snapshot, "run": run}
    return built


def profiles_of(batch_id):
    with store.engine().connect() as connection:
        return dict(
            connection.execute(
                text(
                    "SELECT entity_key, sha256_hex(profile_version) FROM identity.profile "
                    "WHERE batch_id = :batch"
                ),
                {"batch": batch_id},
            ).all()
        )


def served(release_id, source_id):
    """Snapshots the release serves observations from for a source, with their count."""
    with store.engine().connect() as connection:
        return dict(
            connection.execute(
                text(
                    "SELECT e.snapshot_id, count(*) FROM serving.evidence e "
                    "WHERE e.release_id = :release AND e.source_id = :source GROUP BY 1"
                ),
                {"release": release_id, "source": source_id},
            ).all()
        )


def test_a_refresh_reaches_the_next_batch_and_no_earlier_release(spec, tmp_path):
    from link_lens import exports, releases

    built = two_sources(spec)
    a, b = built["source-a"], built["source-b"]
    # Extracting the snapshot a source was onboarded on needs no run of its own.
    assert refresh.extract("source-a")["run_id"] == a["run"]["id"]
    assert refresh.extract("source-b")["run_id"] == b["run"]["id"]
    assert refresh.current_runs() == [a["run"]["id"], b["run"]["id"]]
    assert count("SELECT count(*) FROM onboarding.run") == 2

    first = refresh.assemble(minimum_profiles=3, cohort_pool_size=100)
    assert first["run_ids"] == [a["run"]["id"], b["run"]["id"]]
    assert first["counts"]["profiles"] == 3
    release_one = releases.create(first["batch_id"], "test reviewer")
    digest = releases.digest(release_one["release_id"])
    assert served(1, "source-a") == {a["snapshot"]["id"]: 6}

    # The publisher of source A changes one row. The shape still fits the mapping.
    rows = [["Alpha Renamed Pty Ltd", ABNS[0]]] + [
        [f"Alpha Entity {n}", abn] for n, abn in enumerate(ABNS) if n
    ]
    newer = snapshot_of(
        "source-a", csv_of(["name", "abn"], rows), "2025-03-01T00:00:00Z"
    )
    assert refresh.check_drift("source-a")["blocking"] is False
    extracted = refresh.extract("source-a")
    assert extracted["snapshot_id"] == newer["id"] and extracted["inserted"] == 6

    # The refresh is a run of its own that carries the approval a person gave.
    run = store.require("runs", extracted["run_id"])
    assert extracted["run_id"] != a["run"]["id"]
    assert (run["status"], run["snapshot_id"], run["model_calls"]) == (
        "completed",
        newer["id"],
        0,
    )
    assert (run["mapping_id"], run["approval_id"], run["refreshes_run_id"]) == (
        a["run"]["mapping_id"],
        a["run"]["approval_id"],
        a["run"]["id"],
    )
    assert count("SELECT count(*) FROM onboarding.run WHERE kind = 'refresh'") == 1
    assert count("SELECT count(*) FROM onboarding.approval") == 2
    # Extracting again records nothing more.
    again = refresh.extract("source-a")
    assert (again["run_id"], again["inserted"]) == (extracted["run_id"], 0)
    assert count("SELECT count(*) FROM onboarding.run") == 3
    assert refresh.current_runs() == [extracted["run_id"], b["run"]["id"]]

    # The next batch is assembled from the new snapshot: same entities, new values.
    second = refresh.assemble(minimum_profiles=3, cohort_pool_size=100)
    assert second["run_ids"] == [extracted["run_id"], b["run"]["id"]]
    before, after = profiles_of(first["batch_id"]), profiles_of(second["batch_id"])
    assert set(before) == set(after) and len(after) == 3
    assert all(before[entity] != after[entity] for entity in before)

    def names(batch_id):
        with store.engine().connect() as connection:
            return connection.execute(
                text(
                    "SELECT string_agg(f.detail::text, ' ') FROM identity.profile_field f "
                    "JOIN identity.profile p ON p.id = f.profile_id WHERE p.batch_id = :batch"
                ),
                {"batch": batch_id},
            ).scalar_one()

    assert "Alpha Renamed Pty Ltd" in names(second["batch_id"])
    assert "Alpha Renamed Pty Ltd" not in names(first["batch_id"])
    assert "Alpha Entity 0" in names(first["batch_id"])
    assert "Alpha Entity 0" not in names(second["batch_id"])

    # The earlier release serves exactly what it served; the new one the new snapshot.
    assert releases.digest(release_one["release_id"]) == digest
    assert served(1, "source-a") == {a["snapshot"]["id"]: 6}
    release_two = releases.create(second["batch_id"], "test reviewer")
    assert release_two["release_id"] == 2
    assert served(2, "source-a") == {newer["id"]: 6}
    assert served(2, "source-b") == served(1, "source-b") == {b["snapshot"]["id"]: 6}
    assert served(1, "source-a") == {a["snapshot"]["id"]: 6}
    with store.engine().connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT snapshot_id FROM serving.source "
                    "WHERE release_id = 2 AND source_id = 'source-a'"
                )
            ).scalar_one()
            == newer["id"]
        )
        changes = connection.execute(
            text("SELECT * FROM analytics.release_profile_changes WHERE release_id = 2")
        ).one()
        assert (
            changes.profiles_added,
            changes.profiles_removed,
            changes.profiles_changed,
        ) == (
            0,
            0,
            3,
        )
        # A refresh is not an onboarding attempt and is not counted as one.
        assert (
            connection.execute(
                text("SELECT count(*) FROM analytics.onboarding_run")
            ).scalar_one()
            == 2
        )
    # A batch with a refresh run exports like any other.
    exported = exports.export(tmp_path / "out", second["batch_id"])
    assert exported and (tmp_path / "out" / "onboarding" / "source-a").is_dir()
