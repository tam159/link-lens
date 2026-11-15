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


# ---------------------------------------------------------------------------
# The assets and sensors, run in process on the test database as the role the
# orchestrator works as. Fixture rows that only a person records (approvals,
# releases) are written before the role is taken.

import json  # noqa: E402

from link_lens import ingestion, refresh, releases, store  # noqa: E402
from link_lens.settings import settings  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from test_identity_ops import assembled  # noqa: E402
from test_refresh import ABNS, Client, approve, csv_of, snapshot_of  # noqa: E402
from test_refresh import source as source  # noqa: E402,F401  (a fixture)

ROLE = "linklens_orchestrator"


@pytest.fixture
def location(monkeypatch):
    monkeypatch.syspath_prepend(str(ORCHESTRATION))
    from link_lens_dagster import definitions

    return definitions


@pytest.fixture
def as_orchestrator(monkeypatch):
    """From here on every library connection has the orchestrator's rights only."""

    def take():
        url = store.engine().url
        limited = create_engine(url, connect_args={"options": f"-c role={ROLE}"})
        monkeypatch.setattr(store, "engine", lambda: limited)
        return limited

    return take


def run(location, assets, instance, partition=None, config=None, **resources):
    from link_lens_dagster.resources import LangGraph, Pipeline

    return dagster.materialize(
        assets,
        instance=instance,
        partition_key=partition,
        run_config={"ops": config or {}},
        resources={"pipeline": Pipeline(), "langgraph": LangGraph(), **resources},
        raise_on_error=False,
    )


def materialised(result):
    return sorted(
        event.asset_key.to_user_string()
        for event in result.get_asset_materialization_events()
    )


def check(result, name):
    return next(
        evaluation
        for evaluation in result.get_asset_check_evaluations()
        if evaluation.check_name == name
    )


def stored(sql):
    with store.engine().connect() as connection:
        return connection.execute(text(sql)).scalar_one()


def unchanged(monkeypatch, snapshot_id):
    """The publisher serves the same bytes: registering returns the stored snapshot."""
    monkeypatch.setattr(
        ingestion,
        "register",
        lambda request: (
            {"id": request.dataset_id},
            store.require("snapshots", snapshot_id),
        ),
    )


def test_an_unchanged_source_does_no_work(
    location, source, as_orchestrator, monkeypatch
):
    from link_lens_dagster.assets.extraction import observations
    from link_lens_dagster.assets.snapshots import snapshot

    unchanged(monkeypatch, source["snapshot"]["id"])
    as_orchestrator()
    instance = dagster.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("source", [source["id"]])

    # The first time, the snapshot is emitted on request and extracted.
    first = run(
        location,
        [snapshot, observations],
        instance,
        source["id"],
        {"snapshot": {"config": {"force": True}}},
    )
    assert first.success
    assert materialised(first) == ["observations", "snapshot"]
    assert check(first, "schema_drift").passed
    assert check(first, "observations_have_records").passed
    assert check(first, "extraction_is_complete").passed
    extraction = next(
        event.materialization.metadata
        for event in first.get_asset_materialization_events()
        if event.asset_key.to_user_string() == "observations"
    )
    assert (extraction["records"].value, extraction["newly_stored"].value) == (3, 6)

    # Same bytes again: no snapshot is emitted and extraction does not run.
    again = run(location, [snapshot, observations], instance, source["id"])
    assert again.success
    assert materialised(again) == []
    assert check(again, "schema_drift").passed
    assert stored("SELECT count(*) FROM evidence.observation") == 6

    # Extracting it once more by hand stores nothing new.
    forced = run(location, [observations], instance, source["id"])
    assert forced.success
    repeat = forced.get_asset_materialization_events()[0].materialization.metadata
    assert repeat["newly_stored"].value == 0
    assert repeat["observation_digest"].value == extraction["observation_digest"].value


def test_drift_stops_at_the_check_and_resumes_after_an_approval(
    location, source, spec, as_orchestrator, monkeypatch
):
    from link_lens_dagster.assets.extraction import observations
    from link_lens_dagster.assets.onboarding import onboarding_request
    from link_lens_dagster.assets.snapshots import snapshot
    from link_lens_dagster.resources import LangGraph

    refresh.extract(source["id"])
    instance = dagster.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("source", [source["id"]])
    drift_sensor = location.defs.resolve_sensor_def("drift_detected")
    approval_sensor = location.defs.resolve_sensor_def("mapping_approved")
    assert drift_sensor.default_status == dagster.DefaultSensorStatus.STOPPED
    # Both sensors start from the present.
    drift_context = dagster.build_sensor_context(instance=instance)
    assert isinstance(drift_sensor(drift_context), dagster.SkipReason)
    approval_context = dagster.build_sensor_context(instance=instance)
    assert isinstance(approval_sensor(approval_context), dagster.SkipReason)

    # The publisher renames a column the approved mapping uses. The download
    # stores the new snapshot, as registering a source does.
    downloaded = []

    def register(request):
        downloaded.append(
            snapshot_of(
                source["id"],
                csv_of(["legal_name", "abn"], [["Entity 9", ABNS[0]]]),
                "2025-03-01T00:00:00Z",
            )
        )
        return {"id": source["id"]}, downloaded[-1]

    monkeypatch.setattr(ingestion, "register", register)
    administrator = store.engine()
    limited = as_orchestrator()

    stopped = run(location, [snapshot, observations], instance, source["id"])
    assert not stopped.success
    assert materialised(stopped) == ["snapshot"]
    changed = downloaded[0]
    drift = check(stopped, "schema_drift")
    assert not drift.passed and drift.metadata["blocking"].value is True
    assert stored("SELECT count(*) FROM evidence.observation") == 6

    # The drift sensor, when someone has turned it on, asks for onboarding.
    request = drift_sensor(
        dagster.build_sensor_context(instance=instance, cursor=drift_context.cursor)
    )
    assert [
        (r.partition_key, r.tags["link_lens/paid"]) for r in request.run_requests
    ] == [(source["id"], "true")]

    client = Client()

    class Server(LangGraph):
        def client(self):
            return client

    asked = run(
        location, [onboarding_request], instance, source["id"], langgraph=Server()
    )
    assert asked.success and len(client.started) == 1
    waiting = store.require(
        "runs",
        asked.get_asset_materialization_events()[0]
        .materialization.metadata["run_id"]
        .value,
    )
    assert (waiting["snapshot_id"], waiting["status"]) == (changed["id"], "new")
    # Requested again, nothing more is started.
    assert run(
        location, [onboarding_request], instance, source["id"], langgraph=Server()
    ).success
    assert len(client.started) == 1

    # Extraction stays blocked, and the orchestrator cannot approve anything itself.
    blocked = run(location, [observations], instance, source["id"])
    assert not blocked.success
    with (
        limited.connect() as connection,
        pytest.raises(Exception, match="permission denied"),
    ):
        connection.execute(
            text(
                "INSERT INTO onboarding.approval (id, decision, extra, created_at) "
                "VALUES ('forged', 'approved', '{}', now())"
            )
        )

    # A person approves a mapping for the new shape (the fixture writes it as
    # the administrator); the approval sensor then asks for extraction.
    monkeypatch.setattr(store, "engine", lambda: administrator)
    spec.subject_label_field = "legal_name"
    spec.fields[0].source_fields = ["legal_name"]
    approve(spec, source["id"], changed, name="second")
    monkeypatch.setattr(store, "engine", lambda: limited)
    wanted = approval_sensor(
        dagster.build_sensor_context(instance=instance, cursor=approval_context.cursor)
    )
    assert [r.partition_key for r in wanted.run_requests] == [source["id"]]
    assert wanted.run_requests[0].run_key.startswith("approval-")

    resumed = run(location, [observations], instance, source["id"])
    assert resumed.success
    assert (
        resumed.get_asset_materialization_events()[0]
        .materialization.metadata["newly_stored"]
        .value
        == 2
    )
    assert stored("SELECT count(*) FROM evidence.observation") == 8


def test_a_batch_is_assembled_the_same_way_twice_and_never_released(
    location, spec, snapshot, as_orchestrator
):
    from link_lens_dagster.assets.identity import identity_batch

    run_ids = assembled(spec, snapshot)
    limited = as_orchestrator()
    instance = dagster.DagsterInstance.ephemeral()
    config = {"identity_batch": {"config": {"run_ids": run_ids}}}
    digests = []
    for _ in range(2):
        result = run(location, [identity_batch], instance, config=config)
        assert result.success
        assert check(result, "selected_fields_cite_evidence").passed
        assert check(result, "counts_match_the_batch").passed
        metadata = result.get_asset_materialization_events()[0].materialization.metadata
        assert metadata["profiles"].value == 50
        digests.append((metadata["batch_id"].value, metadata["profile_digest"].value))
    # Two batches, the same profile versions: assembly is deterministic.
    assert digests[0][0] != digests[1][0] and digests[0][1] == digests[1][1]
    assert stored("SELECT count(*) FROM ops.batch") == 2
    # The role the assets work as cannot record a release of either.
    with pytest.raises(Exception, match="permission denied"):
        releases.create(digests[0][0], "not a person")
    with limited.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM ops.release")).scalar_one()
            == 0
        )


def test_the_library_must_be_working_as_the_orchestrator(location, source):
    from link_lens_dagster.assets.extraction import observations

    instance = dagster.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("source", [source["id"]])
    refused = run(location, [observations], instance, source["id"])
    assert not refused.success
    assert stored("SELECT count(*) FROM evidence.observation") == 0


def test_a_recorded_release_requests_the_models_and_their_tests(
    location, spec, snapshot, monkeypatch, tmp_path
):
    from link_lens.pipeline import assemble
    from link_lens_dagster.assets import models as dbt_models

    instance = dagster.DagsterInstance.ephemeral()
    sensor = location.defs.resolve_sensor_def("release_recorded")
    first = dagster.build_sensor_context(instance=instance)
    assert isinstance(sensor(first), dagster.SkipReason)
    assert json.loads(first.cursor) == {"id": 0}

    # A person records a release with the CLI's function.
    batch = assemble(assembled(spec, snapshot))
    release = releases.create(batch["id"], "test reviewer")
    wanted = sensor(
        dagster.build_sensor_context(instance=instance, cursor=first.cursor)
    )
    assert [(r.run_key, r.tags["link_lens/release"]) for r in wanted.run_requests] == [
        (f"release-{release['release_id']}", str(release["release_id"]))
    ]
    assert sensor.job_name == "build_models"
    # Seen once: the next evaluation asks for nothing.
    assert isinstance(
        sensor(dagster.build_sensor_context(instance=instance, cursor=wanted.cursor)),
        dagster.SkipReason,
    )

    # The requested job builds every dbt model and runs every dbt test.
    monkeypatch.setenv(
        "LINK_LENS_DATABASE_URL",
        store.engine().url.render_as_string(hide_password=False),
    )
    settings.cache_clear()
    built = dagster.materialize(
        [dbt_models.models],
        instance=instance,
        resources={"dbt": dbt_models.dbt},
        raise_on_error=False,
    )
    assert built.success
    keys = materialised(built)
    assert "serving/profile" in keys and "analytics/release_overview" in keys
    assert len(keys) == 49
    evaluations = built.get_asset_check_evaluations()
    assert len(evaluations) > 100 and all(e.passed for e in evaluations)
    assert stored("SELECT profiles FROM analytics.release_overview") == 50


def test_other_sensors_report_and_keep_partitions(location, source):
    instance = dagster.DagsterInstance.ephemeral()
    partitions = location.defs.resolve_sensor_def("registered_sources")
    added = partitions(dagster.build_sensor_context(instance=instance))
    assert added.dynamic_partitions_requests[0].partition_keys == [source["id"]]
    instance.add_dynamic_partitions("source", [source["id"]])
    assert isinstance(
        partitions(dagster.build_sensor_context(instance=instance)), dagster.SkipReason
    )
    promoted = location.defs.resolve_sensor_def("ontology_promoted")
    context = dagster.build_sensor_context(instance=instance)
    assert isinstance(promoted(context), dagster.SkipReason)
    assert not promoted.targets  # it can start nothing


def test_orchestration_code_never_records_a_human_decision():
    """No asset or sensor calls what records an approval, a promotion or a release."""
    forbidden = (
        "releases.create",
        "release create",
        "ontology.activate",
        ".promote(",
        "bundles.set_scope",
        "bundles.build",
        'put("approvals"',
        "access.",
        "INSERT INTO",
        "UPDATE ",
        "DELETE ",
    )
    for path in (ORCHESTRATION / "link_lens_dagster").rglob("*.py"):
        code = path.read_text()
        for needle in forbidden:
            assert needle not in code, f"{path.name} mentions {needle}"
    # Paid steps are never retried by Dagster and never start by themselves.
    definitions = (ORCHESTRATION / "link_lens_dagster/assets/onboarding.py").read_text()
    assert "retry_policy" not in definitions


def test_a_refreshed_source_flows_into_the_next_batch(
    location, spec, as_orchestrator, monkeypatch
):
    """Through the assets: new bytes, a refresh run, and a batch assembled from it."""
    from link_lens_dagster.assets.extraction import observations
    from link_lens_dagster.assets.identity import identity_batch
    from link_lens_dagster.assets.snapshots import snapshot
    from test_refresh import two_sources

    built = two_sources(spec)
    onboarded = built["source-a"]["run"]["id"]
    downloaded = []

    def register(request):
        rows = [["Alpha Renamed Pty Ltd", ABNS[0]]] + [
            [f"Alpha Entity {n}", abn] for n, abn in enumerate(ABNS) if n
        ]
        downloaded.append(
            snapshot_of(
                "source-a", csv_of(["name", "abn"], rows), "2025-03-01T00:00:00Z"
            )
        )
        return {"id": "source-a"}, downloaded[-1]

    monkeypatch.setattr(ingestion, "register", register)
    as_orchestrator()
    instance = dagster.DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("source", ["source-a", "source-b"])

    refreshed = run(location, [snapshot, observations], instance, "source-a")
    assert refreshed.success and materialised(refreshed) == ["observations", "snapshot"]
    assert check(refreshed, "schema_drift").passed
    extraction = next(
        event.materialization.metadata
        for event in refreshed.get_asset_materialization_events()
        if event.asset_key.to_user_string() == "observations"
    )
    refresh_run = extraction["run_id"].value
    assert refresh_run != onboarded
    assert store.require("runs", refresh_run)["snapshot_id"] == downloaded[0]["id"]

    config = {
        "identity_batch": {"config": {"minimum_profiles": 3, "cohort_pool_size": 100}}
    }
    batch = run(location, [identity_batch], instance, config=config)
    assert batch.success
    assert check(batch, "selected_fields_cite_evidence").passed
    batch_id = (
        batch.get_asset_materialization_events()[0]
        .materialization.metadata["batch_id"]
        .value
    )
    assert store.require("batches", batch_id)["run_ids"] == [
        refresh_run,
        built["source-b"]["run"]["id"],
    ]
    # Still nothing a client can see: no release exists, and the role cannot make one.
    assert stored("SELECT count(*) FROM ops.release") == 0
