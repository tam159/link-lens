"""The operations console: sign-in, roles, the audit log, and that it does what the CLI does.

Every test works on the database as `linklens_pipeline`, the role the console
runs as, so a right the console needs and does not have fails here first.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from link_lens import ingestion, logs, refresh, releases, sources, store
from link_lens.admin import app as console
from link_lens.admin import audit, auth
from link_lens.contracts import content_hash
from link_lens.settings import settings
from sqlalchemy import create_engine, text
from test_refresh import ABNS, Client, csv_of, two_sources
from typer.testing import CliRunner

PEOPLE = {
    "token-of-eve": {"name": "Eve Engineer", "role": "engineer"},
    "token-of-pat": {"name": "Pat Owner", "role": "product_owner"},
    "token-of-ada": {"name": "Ada Admin", "role": "admin"},
}
EVE, PAT, ADA = (
    {"Authorization": f"Bearer {token}"}
    for token in ("token-of-eve", "token-of-pat", "token-of-ada")
)
STATIC = Path(console.__file__).parent / "static"

DATASET = {
    "id": "dataset-console",
    "name": "console-fixture-register",
    "title": "Console fixture register",
    "notes": "A register used by the console's tests.",
    "license_title": "Creative Commons Attribution 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "organization": {"title": "Fixture Publisher"},
    "resources": [
        {
            "id": "resource-console",
            "name": "register.csv",
            "format": "CSV",
            "url": "https://data.example.org/register.csv",
            "last_modified": "2025-01-05T00:00:00",
        }
    ],
}
BYTES = csv_of(["name", "abn"], [[f"Entity {n}", abn] for n, abn in enumerate(ABNS)])


@pytest.fixture(autouse=True)
def people(isolated_store, monkeypatch):
    monkeypatch.setenv("LINK_LENS_ADMIN_USERS", json.dumps(PEOPLE))
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "10")
    settings.cache_clear()


@pytest.fixture(autouse=True)
def as_pipeline(people, monkeypatch):
    """Every library connection has the rights of the role the console runs as."""
    limited = create_engine(
        store.engine().url, connect_args={"options": "-c role=linklens_pipeline"}
    )
    monkeypatch.setattr(store, "engine", lambda: limited)
    yield
    limited.dispose()


@pytest.fixture
def onboarding():
    """Stands in for the LangGraph server."""
    return Client()


@pytest.fixture
def api(onboarding):
    console.app.dependency_overrides[console.langgraph] = lambda: onboarding
    with TestClient(console.app) as client:
        yield client
    console.app.dependency_overrides.clear()


@pytest.fixture
def publisher(monkeypatch):
    """A portal with one dataset, and its file. Records what was asked of it."""
    asked = []

    def action(portal, name, **parameters):
        asked.append((name, parameters))
        assert name == "package_show" and parameters["id"] == DATASET["id"]
        return DATASET

    def download(url, **options):
        asked.append(("download", url))
        return BYTES, {
            "url": url,
            "bytes": len(BYTES),
            "partial": False,
            "retrieved_at": store.now(),
        }

    monkeypatch.setattr(ingestion, "action", action)
    monkeypatch.setattr(ingestion, "download", download)
    store.put(
        "sources",
        DATASET["id"],
        {
            "id": DATASET["id"],
            "slug": DATASET["name"],
            "metadata": DATASET,
            "portal": "https://data.gov.au/data",
        },
        kind="catalogue",
    )
    return asked


def count(sql, **parameters):
    with store.engine().connect() as connection:
        return connection.execute(text(sql), parameters).scalar_one()


def stored():
    """How much the store holds, to show that a preview adds nothing."""
    return {
        table: count(f"SELECT count(*) FROM {table}")
        for table in (
            "catalog.source",
            "catalog.snapshot",
            "catalog.artifact",
            "catalog.source_refresh",
            "onboarding.run",
            "ops.release",
            "serving.okf_page",
            "ops.admin_action",
        )
    }


def actions(api):
    return api.get("/admin/actions", headers=ADA).json()


def test_nothing_under_admin_answers_without_a_sign_in(api, monkeypatch):
    routes = [
        (method, route.path.replace("{", "").replace("}", ""))
        for route in console.app.routes
        if getattr(route, "path", "").startswith("/admin")
        for method in route.methods
        if (method, route.path)
        not in {("POST", "/admin/session"), ("DELETE", "/admin/session")}
    ]
    assert len(routes) == 19
    for method, path in routes:
        assert api.request(method, path).status_code == 401, (method, path)
        wrong = api.request(method, path, headers={"Authorization": "Bearer nobody"})
        assert wrong.status_code == 401, (method, path)
    assert api.post("/admin/session", json={"token": "nobody"}).status_code == 401
    # With no one configured, no token signs in: there is no default account.
    # Nor does a list that cannot be read, or one that names a role nobody has.
    for listed in (
        "",
        "{}",
        "not json",
        '{"token-of-ada": {"name": "Ada", "role": "root"}}',
    ):
        monkeypatch.setenv("LINK_LENS_ADMIN_USERS", listed)
        settings.cache_clear()
        assert api.get("/admin/me", headers=ADA).status_code == 401, listed
    assert count("SELECT count(*) FROM ops.admin_action") == 0


def test_a_role_is_checked_in_the_api_and_a_refused_change_is_recorded(api):
    assert api.get("/admin/me", headers=PAT).json()["role"] == "product_owner"
    owner_may_not = [
        ("POST", "/admin/clients", {"name": "Acme", "tier_id": "free"}),
        ("PATCH", "/admin/clients/c1", {"status": "suspended"}),
        ("POST", "/admin/clients/c1/keys", {}),
        ("DELETE", "/admin/keys/abcdef", None),
        ("PUT", "/admin/tiers/free", {"rate_per_minute": 10}),
        ("GET", "/admin/clients", None),
        ("GET", "/admin/actions", None),
    ]
    engineer_may_not = [
        ("GET", "/admin/catalogue", None),
        ("POST", "/admin/sources/preview", {"dataset_id": "d"}),
        ("POST", "/admin/sources", {"dataset_id": "d", "confirm_paid_calls": True}),
        ("PATCH", "/admin/sources/s", {"paused": True}),
        ("GET", "/admin/releases/preview?batch_id=b", None),
        ("POST", "/admin/releases", {"batch_id": "b"}),
    ]
    for headers, refused in (
        (PAT, owner_may_not),
        (EVE, engineer_may_not + owner_may_not),
    ):
        for method, path, body in refused:
            answer = api.request(method, path, headers=headers, json=body)
            assert answer.status_code == 403, (method, path, answer.text)
    # An engineer reads; nothing above changed anything.
    for path in (
        "/admin/home",
        "/admin/sources",
        "/admin/releases",
        "/admin/ontology/versions",
    ):
        assert api.get(path, headers=EVE).status_code == 200, path
    assert count("SELECT count(*) FROM access.tier") == 0
    assert count("SELECT count(*) FROM access.client") == 0
    # Each refused change is in the log with who asked and in which role.
    refused = [row for row in actions(api) if row["outcome"] == "refused"]
    assert {(row["actor"], row["role"], row["action"]) for row in refused} >= {
        ("Pat Owner", "product_owner", "key.issue"),
        ("Pat Owner", "product_owner", "tier.set"),
        ("Eve Engineer", "engineer", "source.register"),
        ("Eve Engineer", "engineer", "release.create"),
    }
    assert all("needs the role" in row["result"]["reason"] for row in refused)


def test_a_browser_session_changes_nothing_without_the_console_header(api):
    store.put(
        "sources",
        "s1",
        {"id": "s1", "slug": "s1", "metadata": {"title": "S1"}},
        kind="registered",
    )
    signed = api.post("/admin/session", json={"token": "token-of-pat"})
    assert signed.json() == {"name": "Pat Owner", "role": "product_owner"}
    cookie = signed.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert api.get("/admin/me").json()["name"] == "Pat Owner"
    # A page of another site can make the browser send the cookie, not the header.
    assert api.patch("/admin/sources/s1", json={"paused": True}).status_code == 403
    assert sources.state("s1")[0]["paused_at"] is None
    changed = api.patch(
        "/admin/sources/s1", json={"paused": True}, headers={auth.CONSOLE_HEADER: "1"}
    )
    assert changed.status_code == 200 and changed.json()["paused"] is True
    assert sources.state("s1")[0]["paused_by"] == "Pat Owner"
    api.delete("/admin/session")
    assert api.get("/admin/me").status_code == 401
    # Signing in is not an action, and a token is never written anywhere.
    with store.engine().connect() as connection:
        log = str(connection.execute(text("SELECT * FROM ops.admin_action")).all())
    assert "token-of-pat" not in log and "source.update" in log


def test_a_product_owner_adds_a_source_end_to_end(api, publisher, onboarding, spec):
    # Search the saved catalogue.
    found = api.get("/admin/catalogue", params={"q": "fixture"}, headers=PAT).json()
    assert found["matches"] == 1
    assert found["datasets"][0]["dataset_id"] == DATASET["id"]
    assert found["datasets"][0]["registered"] is False
    assert found["datasets"][0]["formats"] == ["CSV"]

    # Preview: the file is fetched and inspected, and nothing is stored.
    before = stored()
    preview = api.post(
        "/admin/sources/preview", json={"dataset_id": DATASET["id"]}, headers=PAT
    )
    assert preview.status_code == 200, preview.text
    preview = preview.json()
    assert preview["licence"] == "Creative Commons Attribution 4.0"
    assert (preview["bytes"], preview["resource"]["format"]) == (len(BYTES), "csv")
    assert preview["inspection"]["preview"][0] == ["name", "abn"]
    assert preview["already_registered"] is False
    assert preview["budget"]["cap_usd"] == 10 and preview["budget"]["affordable"]
    assert stored() == before
    assert (
        not list((settings().artifact_dir).rglob("*"))
        or before["catalog.artifact"] == 0
    )

    # Confirming needs the paid calls acknowledged.
    unconfirmed = api.post(
        "/admin/sources", json={"dataset_id": DATASET["id"]}, headers=PAT
    )
    assert (
        unconfirmed.status_code == 400
        and "paid model calls" in unconfirmed.json()["detail"]
    )
    assert stored() == before and not onboarding.started

    added = api.post(
        "/admin/sources",
        json={
            "dataset_id": DATASET["id"],
            "resource_id": "resource-console",
            "confirm_paid_calls": True,
        },
        headers=PAT,
    )
    assert added.status_code == 201, added.text
    added = added.json()
    assert added["source_id"] == DATASET["id"] and added["onboarding_started"] is True
    run = store.require("runs", added["run_id"])
    assert (run["status"], run["thread_id"], run["snapshot_id"]) == (
        "new",
        "thread-1",
        added["snapshot_id"],
    )
    assert onboarding.started[0][1]["input"]["run_id"] == added["run_id"]
    # Asking again registers nothing new and starts no second run.
    again = api.post(
        "/admin/sources",
        json={"dataset_id": DATASET["id"], "confirm_paid_calls": True},
        headers=PAT,
    ).json()
    assert (again["onboarding_started"], again["run_id"]) == (False, added["run_id"])
    assert (
        len(onboarding.started) == 1
        and count("SELECT count(*) FROM onboarding.run") == 1
    )

    # The agent proposes a mapping and stops at the Inbox: the source waits for review.
    spec.ontology_hash = run["ontology_hash"]
    mapping = {
        "id": f"{run['id']}:1",
        "run_id": run["id"],
        "config": spec.model_dump(),
        "config_hash": content_hash(spec),
        "version": 1,
    }
    store.put("mappings", mapping["id"], mapping, run["id"])
    run.update(status="needs_review", mapping_id=mapping["id"])
    store.put("runs", run["id"], run, DATASET["id"], "onboarding")
    waiting = api.get(f"/admin/sources/{DATASET['id']}", headers=EVE).json()
    assert waiting["waiting_for_review"] is True and waiting["waiting_since"]
    assert waiting["links"]["inbox"] == "http://localhost:3000"
    assert [row["status"] for row in waiting["runs"]] == ["needs_review"]
    assert [
        row["source_id"]
        for row in api.get("/admin/home", headers=EVE).json()["attention"]
    ] == [DATASET["id"]]

    # A reviewer accepts in the Inbox (a fixture here); the owner sets a cadence.
    approval = {
        "id": f"{run['id']}-approval",
        "run_id": run["id"],
        "mapping_id": mapping["id"],
        "decision": "approved",
        "config_hash": mapping["config_hash"],
        "reviewer": "TEST FIXTURE; NOT HUMAN EVALUATION",
    }
    store.put("approvals", approval["id"], approval, run["id"])
    run.update(status="completed", approval_id=approval["id"])
    store.put("runs", run["id"], run, DATASET["id"], "onboarding")
    fresh = api.patch(
        f"/admin/sources/{DATASET['id']}", json={"cadence_days": 7}, headers=PAT
    ).json()
    assert (fresh["refresh_status"], fresh["waiting_for_review"]) == ("fresh", False)
    assert fresh["approved_config_hash"] == mapping["config_hash"]
    assert fresh["cadence_days"] == 7 and fresh["links"]["inbox"] is None
    assert api.get("/admin/home", headers=EVE).json()["attention"] == []
    listed = api.get("/admin/catalogue", params={"q": "fixture"}, headers=PAT).json()
    assert listed["datasets"][0]["registered"] is True

    # Every change is in the log, with who made it.
    log = [
        (row["action"], row["actor"], row["role"], row["target"], row["outcome"])
        for row in actions(api)
    ]
    assert log == [
        ("source.update", "Pat Owner", "product_owner", DATASET["id"], "done"),
        ("source.register", "Pat Owner", "product_owner", DATASET["id"], "done"),
        ("source.register", "Pat Owner", "product_owner", DATASET["id"], "done"),
    ]
    assert [row["action"] for row in fresh["actions"]] == [
        "source.update",
        "source.register",
        "source.register",
    ]


def test_cadence_and_pause_are_the_registry_rows_dagster_reads(api):
    store.put(
        "sources",
        "s1",
        {"id": "s1", "slug": "s1", "metadata": {"title": "S1"}},
        kind="registered",
    )
    assert (
        api.patch(
            "/admin/sources/s1", json={"cadence_days": 2.5, "paused": True}, headers=PAT
        ).status_code
        == 200
    )
    by_console = sources.state("s1")[0]
    assert (by_console["cadence_days"], by_console["paused_by"]) == (2.5, "Pat Owner")
    # The same through the library the CLI calls gives the same row.
    sources.resume("s1")
    sources.set_cadence("s1", None)
    cleared = api.patch(
        "/admin/sources/s1", json={"cadence_days": 2.5}, headers=PAT
    ).json()
    assert cleared["cadence_days"] == 2.5 and cleared["paused"] is False
    assert (
        api.patch("/admin/sources/s1", json={"cadence_days": None}, headers=PAT).json()[
            "cadence_days"
        ]
        is None
    )
    assert (
        api.patch(
            "/admin/sources/s1", json={"cadence_days": 0}, headers=PAT
        ).status_code
        == 422
    )
    assert (
        api.patch(
            "/admin/sources/unknown", json={"paused": True}, headers=PAT
        ).status_code
        == 404
    )
    assert api.get("/admin/sources/unknown", headers=EVE).status_code == 404


def test_a_source_is_refused_when_the_budget_would_be_exceeded(
    api, publisher, onboarding, monkeypatch
):
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "0")
    settings.cache_clear()
    before = stored()
    preview = api.post(
        "/admin/sources/preview", json={"dataset_id": DATASET["id"]}, headers=PAT
    ).json()
    assert (
        preview["budget"]["affordable"] is False
        and preview["budget"]["remaining_usd"] == 0
    )
    refused = api.post(
        "/admin/sources",
        json={"dataset_id": DATASET["id"], "confirm_paid_calls": True},
        headers=PAT,
    )
    assert (
        refused.status_code == 409
        and "budget would be exceeded" in refused.json()["detail"]
    )
    after = stored()
    assert after.pop("ops.admin_action") == 1 and before.pop("ops.admin_action") == 0
    assert after == before and not onboarding.started
    assert (
        count("SELECT kind FROM catalog.source WHERE id = :id", id=DATASET["id"])
        == "catalogue"
    )
    (row,) = actions(api)
    assert (row["action"], row["outcome"], row["actor"]) == (
        "source.register",
        "refused",
        "Pat Owner",
    )


def test_a_release_from_the_console_is_the_release_the_cli_records(api, spec):
    from link_lens.cli import app as cli

    two_sources(spec)
    refresh.extract("source-a")
    refresh.extract("source-b")
    batch = refresh.assemble(minimum_profiles=3, cohort_pool_size=100)["batch_id"]

    listed = api.get("/admin/releases", headers=EVE).json()
    assert listed["releases"] == [] and [
        row["batch_id"] for row in listed["batches"]
    ] == [batch]

    # The comparison writes nothing, and is what the CLI prints.
    before = stored()
    preview = api.get(
        "/admin/releases/preview", params={"batch_id": batch}, headers=PAT
    ).json()
    assert (
        preview["profiles"],
        preview["profiles_added"],
        preview["current_release_id"],
    ) == (3, 3, None)
    assert preview["ready"] and all(check["passed"] for check in preview["checks"])
    assert stored() == before
    printed = CliRunner().invoke(cli, ["release", "preview", "--batch-id", batch])
    assert printed.exit_code == 0 and json.loads(printed.stdout) == preview

    made = api.post(
        "/admin/releases", json={"batch_id": batch, "notes": "first"}, headers=PAT
    )
    assert made.status_code == 201, made.text
    by_console = made.json()
    assert (by_console["release_id"], by_console["released_by"]) == (1, "Pat Owner")

    # The same decision through the CLI, as the same person.
    by_cli = CliRunner().invoke(
        cli,
        [
            "release",
            "create",
            "--batch-id",
            batch,
            "--reviewer",
            "Pat Owner",
            "--notes",
            "first",
        ],
    )
    assert by_cli.exit_code == 0, by_cli.output
    by_cli = json.loads(by_cli.stdout)
    different = {key for key in by_console if by_console[key] != by_cli[key]}
    # The ID and the two times are all that tell them apart.
    assert different == {"release_id", "released_at", "generated_at"}
    assert releases.digest(1)["digest"] == releases.digest(2)["digest"]
    first, second = releases.show(1), releases.show(2)
    assert (first["pages"], first["index_pages"]) == (
        second["pages"],
        second["index_pages"],
    )
    with store.engine().connect() as connection:
        rows = connection.execute(
            text(
                "SELECT batch_id, ontology_hash, released_by, notes FROM ops.release ORDER BY id"
            )
        ).all()
    # One row each in the table Dagster's release sensor watches, alike but for ID and time.
    assert len(rows) == 2 and rows[0] == rows[1]

    after = api.get(
        "/admin/releases/preview", params={"batch_id": batch}, headers=PAT
    ).json()
    assert after["ready"] is False and after["profiles_unchanged"] == 3
    (logged,) = [row for row in actions(api) if row["action"] == "release.create"]
    assert (logged["actor"], logged["target"], logged["result"]["release_id"]) == (
        "Pat Owner",
        batch,
        1,
    )
    # A batch that cannot be released is refused by the library, and that is recorded too.
    bad = api.post("/admin/releases", json={"batch_id": "no-such-batch"}, headers=PAT)
    assert bad.status_code == 404
    assert actions(api)[0]["outcome"] == "failed"


def test_clients_tiers_and_keys_and_no_key_material_in_any_log(api, monkeypatch):
    from link_lens.cli import app as cli

    lines = []
    monkeypatch.setattr(
        logs, "event", lambda name, **fields: lines.append((name, fields))
    )

    tier = api.put(
        "/admin/tiers/standard",
        json={
            "rate_per_minute": 30,
            "monthly_quota": 1000,
            "interfaces": ["rest", "mcp"],
        },
        headers=ADA,
    )
    assert tier.status_code == 200 and tier.json()["rate_per_minute"] == 30
    assert (
        api.put(
            "/admin/tiers/odd",
            json={"rate_per_minute": 5, "interfaces": ["fax"]},
            headers=ADA,
        ).status_code
        == 400
    )
    client = api.post(
        "/admin/clients", json={"name": "Acme", "tier_id": "standard"}, headers=ADA
    ).json()
    assert (
        api.post(
            "/admin/clients", json={"name": "Nobody", "tier_id": "missing"}, headers=ADA
        ).status_code
        == 404
    )

    issued = api.post(
        f"/admin/clients/{client['client_id']}/keys",
        json={"label": "laptop"},
        headers=ADA,
    )
    assert issued.status_code == 201 and issued.headers["cache-control"] == "no-store"
    key = issued.json()
    prefix, secret = key["key"].split("_")[1:]
    assert prefix == key["prefix"] and len(secret) == 64

    # The key is shown once: no later answer carries it.
    listed = api.get("/admin/clients", headers=ADA)
    assert secret not in listed.text and "key_hash" not in listed.text
    (shown,) = listed.json()["clients"]
    assert shown["keys"] == [
        {**shown["keys"][0], "prefix": prefix, "label": "laptop", "revoked_at": None}
    ]

    changed = api.patch(
        f"/admin/clients/{client['client_id']}",
        json={"status": "suspended"},
        headers=ADA,
    )
    assert changed.json()["status"] == "suspended"
    assert (
        api.patch(
            f"/admin/clients/{client['client_id']}",
            json={"status": "gone"},
            headers=ADA,
        ).status_code
        == 422
    )
    # The CLI's equivalent changes the same row.
    back = CliRunner().invoke(
        cli, ["access", "client", "set", client["client_id"], "--status", "active"]
    )
    assert back.exit_code == 0, back.output
    assert (
        json.loads(CliRunner().invoke(cli, ["access", "client", "list"]).stdout)[0][
            "status"
        ]
        == "active"
    )

    # Revoking keeps the row.
    revoked = api.delete(f"/admin/keys/{prefix}", headers=ADA)
    assert revoked.status_code == 200 and revoked.json()["revoked_at"]
    assert (
        count("SELECT count(*) FROM access.api_key WHERE revoked_at IS NOT NULL") == 1
    )
    assert api.delete("/admin/keys/unknown", headers=ADA).status_code == 404

    log = actions(api)
    assert [(row["action"], row["outcome"]) for row in log] == [
        ("key.revoke", "failed"),
        ("key.revoke", "done"),
        ("client.update", "done"),
        ("key.issue", "done"),
        ("client.create", "failed"),
        ("client.create", "done"),
        ("tier.set", "failed"),
        ("tier.set", "done"),
    ]
    assert all((row["actor"], row["role"]) == ("Ada Admin", "admin") for row in log)
    issue = log[3]
    assert issue["target"] == client["client_id"] and issue["result"] == {
        "key_id": key["key_id"],
        "prefix": prefix,
    }
    # Neither the key, its secret, its hash nor an admin's token is in the table or a log line.
    with store.engine().connect() as connection:
        table = str(connection.execute(text("SELECT * FROM ops.admin_action")).all())
        digest = connection.execute(
            text("SELECT sha256_hex(key_hash) FROM access.api_key")
        ).scalar_one()
    for written in (table, json.dumps(lines, default=str), json.dumps(log)):
        for material in (secret, key["key"], digest, "token-of-ada"):
            assert material not in written
    assert ("console.action", "key.issue") in {
        (name, fields.get("action")) for name, fields in lines
    }


def test_the_log_is_append_only_and_shows_a_request_that_never_finished(api, database):
    ada = auth.Principal("Ada Admin", "admin")
    audit.write(
        ada,
        "tier.set",
        "cut-off",
        {"rate_per_minute": 1, "api_key": "x", "nested": {"secret": "y"}},
        "requested",
    )
    (row,) = actions(api)
    assert (row["outcome"], row["finished_at"]) == ("unfinished", None)
    assert row["request"] == {"rate_per_minute": 1, "nested": {}}
    with pytest.raises(Exception, match="append-only|cannot be updated|forbid"):
        with store.engine().begin() as connection:
            connection.execute(
                text("UPDATE ops.admin_action SET actor = 'someone else'")
            )
    with store.engine().connect() as connection:
        may = connection.execute(
            text(
                "SELECT has_table_privilege('linklens_orchestrator', 'ops.admin_action', p) "
                "FROM unnest(ARRAY['INSERT', 'UPDATE', 'DELETE']) AS p"
            )
        ).scalars()
        assert not any(may)
        assert not connection.execute(
            text(
                "SELECT has_table_privilege('linklens_pipeline', 'ops.admin_action', 'DELETE')"
            )
        ).scalar_one()


def test_the_pages_call_only_the_admin_api_and_hold_no_credentials(api):
    page = api.get("/console/")
    assert page.status_code == 200 and "console.js" in page.text
    assert "default-src 'self'" in page.headers["content-security-policy"]
    assert api.get("/", follow_redirects=False).headers["location"] == "/console/"
    files = {path.name: path.read_text() for path in STATIC.iterdir()}
    assert set(files) == {"index.html", "console.css", "console.js"}
    script = files["console.js"]
    # One place talks to a server, and only to /admin on the console's own origin.
    assert script.count("fetch(") == 1 and 'fetch("/admin" + path' in script
    # A publisher's metadata can hold any address; only web addresses become links.
    assert "/^https?:\\/\\//i.test(href)" in script
    for word in (
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "innerHTML",
        "eval(",
        "localStorage",
    ):
        assert word not in script
    for text_ in files.values():
        lowered = text_.lower()
        for word in (
            "postgres",
            "psycopg",
            "link_lens_",
            "password=",
            "5439",
            "bearer",
        ):
            assert word not in lowered, word
    assert (
        "http://" not in files["index.html"] and "https://" not in files["index.html"]
    )
    # The API serves no description of itself to someone not signed in.
    assert (
        api.get("/openapi.json").status_code == 404
        and api.get("/docs").status_code == 404
    )


def test_ontology_versions_are_listed_read_only(api):
    from link_lens import ontology

    ontology.register(ontology.legacy())
    versions = api.get("/admin/ontology/versions", headers=EVE).json()
    assert [version["ontology_hash"] for version in versions] == [
        ontology.digest(ontology.legacy())
    ]
    assert versions[0]["gate"] is None and versions[0]["activations"] == []
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert (
            api.request(method, "/admin/ontology/versions", headers=ADA).status_code
            == 405
        )
