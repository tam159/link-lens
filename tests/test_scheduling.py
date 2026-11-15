"""What a schedule runs on: due sources, backoff, pause, conditional downloads, backfill, alerts."""

import json
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from link_lens import alerts, ingestion, refresh, sources, store
from link_lens.settings import settings
from sqlalchemy import text
from test_refresh import ABNS, approve, csv_of, snapshot_of
from test_refresh import source as source  # noqa: F401  (a fixture)

T0 = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)


def ids(found):
    return [row["source_id"] for row in found]


def registered(spec, source_id, portal="https://data.gov.au/data"):
    store.put(
        "sources",
        source_id,
        {
            "id": source_id,
            "slug": source_id,
            "portal": portal,
            "metadata": {"title": source_id},
        },
        kind="registered",
    )
    snapshot = snapshot_of(
        source_id,
        csv_of(["name", "abn"], [[source_id, ABNS[0]]]),
        "2025-02-01T00:00:00Z",
    )
    approve(spec, source_id, snapshot)


def test_a_source_is_due_by_its_cadence_and_not_while_paused(source):
    assert sources.due(T0) == []  # no cadence: nobody asked for it to be checked
    sources.set_cadence(source["id"], 1)
    assert ids(sources.due(T0)) == [source["id"]]  # never checked
    sources.record_check(source["id"], T0)
    assert sources.due(T0 + timedelta(hours=23)) == []
    due = sources.due(T0 + timedelta(days=1))
    assert ids(due) == [source["id"]] and due[0]["host"] == "data.gov.au"

    paused = sources.pause(source["id"], "owner")
    assert paused["paused_at"] and paused["paused_by"] == "owner"
    assert sources.due(T0 + timedelta(days=30)) == []
    assert sources.overdue(T0 + timedelta(days=30)) == []  # a decision, not a fault
    with pytest.raises(ValueError, match="name of the person"):
        sources.pause(source["id"], " ")
    assert sources.resume(source["id"])["paused_at"] is None
    assert ids(sources.due(T0 + timedelta(days=30))) == [source["id"]]
    late = sources.overdue(T0 + timedelta(days=30))
    assert late[0]["reason"] == "not checked since it became due"


def test_failures_back_off_and_a_success_ends_them(source):
    sources.set_cadence(source["id"], 1)
    sources.record_check(source["id"], T0)
    due_at = T0 + timedelta(days=1)
    first = sources.record_failure(
        source["id"], "RuntimeError: Download failed", due_at
    )
    assert first["consecutive_failures"] == 1
    assert sources.due(due_at + timedelta(minutes=59)) == []
    assert ids(sources.due(due_at + timedelta(hours=1))) == [source["id"]]
    second = sources.record_failure(
        source["id"], "RuntimeError: again", due_at + timedelta(hours=1)
    )
    assert second["consecutive_failures"] == 2
    assert sources.due(due_at + timedelta(hours=2, minutes=59)) == []
    assert ids(sources.due(due_at + timedelta(hours=3))) == [source["id"]]
    # Three in a row is worth telling someone, whatever the clock says.
    sources.record_failure(
        source["id"], "RuntimeError: still", due_at + timedelta(hours=3)
    )
    late = sources.overdue(due_at + timedelta(hours=3))
    assert (
        late[0]["consecutive_failures"] == 3
        and "RuntimeError: still" in late[0]["reason"]
    )
    # The wait never exceeds the cadence.
    for _ in range(8):
        last = sources.record_failure(source["id"], "x", due_at + timedelta(hours=3))
    assert ids(sources.due(due_at + timedelta(hours=3) + timedelta(days=1)))
    assert last["consecutive_failures"] == 11
    # The publisher answers again.
    ok = sources.record_check(source["id"], due_at + timedelta(days=2))
    assert ok["consecutive_failures"] == 0 and ok["retry_after"] is None


def test_a_failed_download_is_counted(source, monkeypatch):
    def unreachable(request):
        raise RuntimeError("Download failed: could not resolve host")

    monkeypatch.setattr(ingestion, "register", unreachable)
    with pytest.raises(RuntimeError, match="could not resolve"):
        refresh.check(source["id"])
    state = sources.state(source["id"])[0]
    assert (
        state["consecutive_failures"] == 1
        and "could not resolve" in state["last_error"]
    )


def test_due_sources_are_capped_per_publisher_host(spec):
    for n in range(5):
        registered(spec, f"gov-{n}")
        sources.set_cadence(f"gov-{n}", 1)
    for n in range(2):
        registered(spec, f"nz-{n}", portal="https://catalogue.data.govt.nz")
        sources.set_cadence(f"nz-{n}", 1)
    assert len(sources.due(T0)) == 7
    capped = sources.due(T0, per_host=2)
    assert sorted(ids(capped)) == ["gov-0", "gov-1", "nz-0", "nz-1"]
    assert len(sources.due(T0, limit=3)) == 3


def curl(responses):
    """Stands in for curl: answers each call from `responses` and records the command."""
    calls = []

    def run(command, **options):
        calls.append(command)
        status, headers, body = responses[min(len(calls), len(responses)) - 1](command)
        out = command[command.index("--output") + 1]
        dump = command[command.index("--dump-header") + 1]
        lines = [f"HTTP/2 {status}"] + [f"{k}: {v}" for k, v in headers.items()]
        with open(dump, "w") as file:
            file.write("\r\n".join(lines) + "\r\n\r\n")
        with open(out, "wb") as file:
            file.write(body)

        class Done:
            returncode = 0
            stderr = b""

        return Done()

    return run, calls


def test_a_download_asks_only_for_something_newer(monkeypatch):
    body = csv_of(["name", "abn"], [["Entity", ABNS[0]]])

    def fresh(command):
        return (
            200,
            {"ETag": '"v1"', "Last-Modified": "Mon, 05 Jan 2026 00:00:00 GMT"},
            body,
        )

    def unchanged(command):
        assert 'If-None-Match: "v1"' in command
        return 304, {"ETag": '"v1"'}, b""

    run, calls = curl([fresh, unchanged])
    monkeypatch.setattr(ingestion.subprocess, "run", run)
    dataset = {
        "id": "conditional",
        "name": "conditional",
        "license_title": "CC BY",
        "resources": [
            {
                "id": "res-1",
                "format": "CSV",
                "url": "https://data.gov.au/file.csv",
                "name": "f",
            }
        ],
    }
    monkeypatch.setattr(ingestion, "action", lambda portal, name, **params: dataset)
    request = ingestion.SourceRequest(dataset_id="conditional", resource_id="res-1")

    _, first = ingestion.register(request)
    assert first["receipt"]["etag"] == '"v1"'
    assert first["receipt"]["last_modified"].startswith("Mon, 05 Jan 2026")
    checked = sources.state("conditional")[0]["last_checked_at"]

    _, second = ingestion.register(request)
    assert second["id"] == first["id"] and len(calls) == 2
    with store.engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM catalog.snapshot")
            ).scalar_one()
            == 1
        )
    assert sources.state("conditional")[0]["last_checked_at"] >= checked
    # Without validators there is nothing conditional about a download.
    with pytest.raises(ValueError, match="empty response"):
        run2, _ = curl([lambda command: (200, {}, b"")])
        monkeypatch.setattr(ingestion.subprocess, "run", run2)
        ingestion.download("https://data.gov.au/file.csv")


def test_backfill_plans_before_it_extracts(source, spec):
    from link_lens.cli import app
    from typer.testing import CliRunner

    plan = refresh.backfill_plan()
    assert [(row["source_id"], row["observations"], row["action"]) for row in plan] == [
        (source["id"], 0, "extract")
    ]
    runner = CliRunner()
    dry = runner.invoke(app, ["source", "backfill"])
    assert dry.exit_code == 0 and json.loads(dry.output)["applied"] is False
    with store.engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM evidence.observation")
            ).scalar_one()
            == 0
        )

    applied = runner.invoke(app, ["source", "backfill", "--apply"])
    assert applied.exit_code == 0
    assert json.loads(applied.output)["sources"][0]["result"]["inserted"] == 6
    assert refresh.backfill_plan()[0]["action"] == "nothing to do"

    # A snapshot the mapping cannot read is reported as blocked, not extracted.
    snapshot_of(
        source["id"],
        csv_of(["legal_name", "abn"], [["E", ABNS[0]]]),
        "2025-03-01T00:00:00Z",
    )
    assert refresh.backfill_plan()[0]["action"] == "extract"  # not checked yet
    blocked = runner.invoke(app, ["source", "backfill", "--apply"])
    assert blocked.exit_code == 3
    assert refresh.backfill_plan(source["id"])[0]["action"].startswith(
        "blocked by drift"
    )


@pytest.fixture
def channel(monkeypatch):
    """A local webhook that keeps what is posted to it, as a team channel would."""
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(
                json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv(
        "LINK_LENS_ALERT_WEBHOOK_URL",
        f"http://127.0.0.1:{server.server_port}/hook/secret-token",
    )
    settings.cache_clear()
    yield received
    server.shutdown()
    settings.cache_clear()


@pytest.fixture
def logged(monkeypatch):
    """What `alerts` writes to the log, as (event, fields)."""
    events = []
    monkeypatch.setattr(
        alerts.logs,
        "event",
        lambda name, level=None, **fields: events.append((name, fields)),
    )
    return events


def test_an_alert_names_the_source_and_links_to_the_run(channel, logged):
    assert alerts.send(
        "run_failed",
        "refresh_source failed",
        source="ASIC - Company Dataset",
        link="http://localhost:3070/runs/abc",
        details={"Error": "Download failed"},
    )
    assert channel == [
        {
            "text": "[Link Lens] Run failed: refresh_source failed\n"
            "Source: ASIC - Company Dataset\nError: Download failed\n"
            "http://localhost:3070/runs/abc"
        }
    ]
    with pytest.raises(ValueError, match="Unknown alert kind"):
        alerts.send("surprise", "x")
    assert [name for name, _ in logged] == ["alert.sent"]
    assert "secret-token" not in json.dumps(logged)


def test_an_alert_without_a_channel_is_logged_and_nothing_fails(monkeypatch, logged):
    monkeypatch.delenv("LINK_LENS_ALERT_WEBHOOK_URL", raising=False)
    settings.cache_clear()
    assert alerts.send("drift", "columns changed", source="a source") is False
    assert logged[-1][0] == "alert.unsent" and logged[-1][1]["source"] == "a source"
    # A channel that does not answer is logged too, and does not raise.
    monkeypatch.setenv(
        "LINK_LENS_ALERT_WEBHOOK_URL", "http://127.0.0.1:9/hook/secret-token"
    )
    settings.cache_clear()
    assert alerts.send("budget", "80% of the cap is spent") is False
    assert logged[-1][0] == "alert.failed"
    assert "secret-token" not in json.dumps(logged)
    settings.cache_clear()
