"""Running as a service: shared limits, the replica, logs, metrics, moved artifacts."""

import io
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from link_lens import artifacts, blobs, releases, store
from link_lens.cli import app as cli
from link_lens.interfaces import mcp_server
from link_lens.product import db, keys, limits, observe
from link_lens.product.app import app
from link_lens.settings import settings
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_product_rest import Clock, clock, key_for, released  # noqa: F401
from typer.testing import CliRunner

CONTRACTS = Path(__file__).parents[1] / "docs" / "api"


@pytest.fixture
def configure(monkeypatch):
    """Set product settings for one test and forget them afterwards."""

    def set_(**values):
        for name, value in values.items():
            monkeypatch.setenv("LINK_LENS_" + name.upper(), value)
        settings.cache_clear()

    yield set_
    monkeypatch.undo()
    settings.cache_clear()
    db.dedicated.cache_clear()


@pytest.fixture
def logged():
    """Fields of every line the service logs, whether or not logging is set up."""
    lines = []

    class Collect(logging.Handler):
        def emit(self, record):
            lines.append(
                {"event": record.getMessage(), **getattr(record, "fields", {})}
            )

    handler, logger = Collect(), logging.getLogger("link_lens")
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield lines
    logger.removeHandler(handler)
    logger.setLevel(level)


def database_url():
    return store.engine().url.render_as_string(hide_password=False)


def test_a_bucket_in_the_database_is_shared_by_every_instance(released):  # noqa: F811
    key_for("shared", rate_per_minute=3)
    with store.engine().connect() as connection:
        key = connection.execute(text("SELECT id FROM access.api_key")).scalar_one()
    time = Clock()
    first, second = limits.DatabaseLimiter(time), limits.DatabaseLimiter(time)

    def take(limiter):
        with db.writer() as connection:
            return limiter.take(connection, str(key), 3)

    assert [take(first), take(second), take(first)] == [None, None, None]
    assert take(second) == pytest.approx(20)  # a token every 20 seconds
    time.now += 10
    assert take(first) == pytest.approx(10)
    time.now += 10
    assert take(first) is None and take(second) == pytest.approx(20)
    time.now += 3600
    assert [take(second) for _ in range(4)][:3] == [None, None, None]

    # Many instances at once never hand out more than the bucket holds.
    time.now += 3600
    with ThreadPoolExecutor(12) as pool:
        granted = list(pool.map(lambda n: take((first, second)[n % 2]), range(24)))
    assert sum(result is None for result in granted) == 3
    # A lower rate for the tier applies at once to what the bucket holds.
    time.now += 3600
    with db.writer() as connection:
        assert first.take(connection, str(key), 1) is None
        assert first.take(connection, str(key), 1) == pytest.approx(60)

    for forbidden in ("DELETE FROM access.rate_bucket", "TRUNCATE access.rate_bucket"):
        with pytest.raises(DBAPIError, match="permission denied"):
            with db.writer() as connection:
                connection.execute(text(forbidden))


def test_the_service_limits_through_the_database_unless_told_otherwise(
    released,  # noqa: F811
    configure,
    monkeypatch,
):
    monkeypatch.setattr(limits, "limiter", None)
    api = TestClient(app)
    headers, _ = key_for("two-a-minute", rate_per_minute=2)
    assert isinstance(limits.configured(), limits.DatabaseLimiter)
    assert [api.get("/v1/sources", headers=headers).status_code for _ in range(3)] == [
        200,
        200,
        429,
    ]
    limited = api.get("/v1/sources", headers=headers)
    assert 25 <= int(limited.headers["retry-after"]) <= 30
    with store.engine().connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM access.rate_bucket")).scalar()
            == 1
        )
    assert [row["calls"] for row in keys.usage()] == [
        2
    ]  # a refused call is not counted

    configure(rate_limit_store="memory")
    assert isinstance(limits.configured(), limits.RateLimiter)


def test_reads_go_to_the_replica_and_the_count_to_the_primary(released, configure):  # noqa: F811
    api = TestClient(app)
    headers, _ = key_for("replicated")
    # A stand-in for a replica: the same database, on connections that cannot write.
    read_only = database_url() + "?options=-c%20default_transaction_read_only%3Don"
    configure(product_replica_url=read_only)
    assert db.replica() is not db.primary() and db.primary() is store.engine()
    with pytest.raises(DBAPIError, match="read-only transaction"):
        with db.session() as connection:
            connection.execute(
                text(
                    "INSERT INTO access.api_usage VALUES (gen_random_uuid(), now(), 'rest', 1)"
                )
            )
    entity = api.get("/v1/entities", params={"limit": 1}, headers=headers)
    assert entity.status_code == 200
    entity_id = entity.json()["entities"][0]["entity_id"]
    for route in (
        f"/v1/entities/{entity_id}/profile",
        "/v1/sources",
        "/v1/okf/index.md",
    ):
        assert api.get(route, headers=headers).status_code == 200
    assert [row["calls"] for row in keys.usage()] == [4]

    # In production the service logs in with a role of its own on the primary.
    configure(product_database_url=database_url() + "?application_name=product")
    assert db.primary() is not store.engine()
    with db.writer() as connection:
        assert (
            connection.execute(text("SELECT current_user")).scalar()
            == "linklens_product"
        )
        assert connection.execute(text("SHOW application_name")).scalar() == "product"
    assert api.get("/v1/sources", headers=headers).status_code == 200


def test_every_request_has_an_id_a_log_line_and_a_metric(released, configure, logged):  # noqa: F811
    api = TestClient(app)
    headers, created = key_for("observed")
    observe.metrics.__init__()
    entity_id = api.get("/v1/entities", params={"limit": 1}, headers=headers).json()[
        "entities"
    ][0]["entity_id"]
    logged.clear()
    if True:
        answer = api.get(
            f"/v1/entities/{entity_id}/profile",
            headers={**headers, "X-Request-ID": "trace-123"},
        )
        made_up = api.get("/v1/sources", headers={"X-Request-ID": "not valid\x7f!"})
        api.get("/health")
    assert answer.headers["x-request-id"] == "trace-123"
    assert len(made_up.headers["x-request-id"]) == 32 and made_up.status_code == 401
    lines = [line for line in logged if line["event"] == "request"]
    assert len(lines) == 2  # the health check is counted, not logged
    assert lines[0] == {
        "event": "request",
        "request_id": "trace-123",
        "interface": "rest",
        "method": "GET",
        "route": "/v1/entities/{entity_id}/profile",
        "status": 200,
        "ms": lines[0]["ms"],
        "key_prefix": created["prefix"],
        "client_id": created["client_id"],
        "tier": "observed",
    }
    assert lines[1]["status"] == 401 and lines[1]["key_prefix"] is None
    # Neither the key nor an entity's ID is in a log line.
    logged = json.dumps(lines)
    assert created["key"] not in logged and created["key"].split("_")[2] not in logged
    assert entity_id not in logged

    assert api.get("/metrics").status_code == 404
    configure(metrics_token="scrape-me")
    assert (
        api.get("/metrics", headers={"Authorization": "Bearer wrong"}).status_code
        == 404
    )
    scraped = api.get("/metrics", headers={"Authorization": "Bearer scrape-me"})
    assert scraped.status_code == 200 and scraped.headers["content-type"].startswith(
        "text/plain"
    )
    body = scraped.text
    assert (
        'linklens_requests_total{interface="rest",tier="observed",status="200"} 2'
        in body
    )
    assert (
        'linklens_requests_total{interface="rest",tier="none",status="401"} 1' in body
    )
    assert (
        'linklens_requests_total{interface="other",tier="none",status="200"} 1' in body
    )
    assert 'linklens_request_seconds_count{interface="rest",tier="observed"} 2' in body
    assert (
        'linklens_request_seconds_bucket{interface="rest",tier="observed",le="+Inf"} 2'
        in body
    )


@pytest.mark.asyncio
async def test_an_mcp_call_is_logged_with_its_tool(released, logged):  # noqa: F811
    from test_product_mcp import both, connected

    headers, created = both()
    logged.clear()
    if True:
        async with connected(headers, "/mcp/files", mode="legacy") as session:
            await session.call_tool("okf_ls", {})
    lines = [line for line in logged if line["event"] == "request"]
    called = [line for line in lines if line.get("tool")]
    assert [(line["tool"], line["interface"], line["route"]) for line in called] == [
        ("okf_ls", "mcp", "/mcp/files")
    ]
    assert called[0]["key_prefix"] == created["prefix"] and called[0]["status"] == 200
    assert all(line["request_id"] for line in lines)


class Bucket:
    """An S3 client that keeps objects in memory."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body):
        self.objects[Bucket, Key] = Body

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Bucket, Key])}


def test_artifacts_move_to_object_storage_with_every_hash_checked(
    tmp_path, monkeypatch
):
    kept = {
        store.blob(body, "text/plain", f"note-{number}.txt"): body
        for number, body in enumerate([b"first", b"second", b"third", b"fourth"])
    }
    with pytest.raises(ValueError, match="LINK_LENS_ARTIFACT_STORE=s3"):
        artifacts.migrate()
    bucket, local = Bucket(), blobs.stores()["local"]
    remote = blobs.S3BlobStore(
        "archive", "link-lens", tmp_path / "cache", client=bucket
    )
    monkeypatch.setattr(blobs, "stores", lambda: {"s3": remote, "local": local})

    def locations():
        with store.engine().connect() as connection:
            return dict(
                connection.execute(
                    text(
                        "SELECT sha256_hex(sha256), split_part(uri, ':', 1) FROM catalog.artifact"
                    )
                ).all()
            )

    planned = artifacts.migrate(dry_run=True)
    assert (planned["moved"], planned["dry_run"]) == (4, True) and not bucket.objects
    assert set(locations().values()) == {"local"}

    # One file is damaged and one is gone before the move.
    damaged, gone, *sound = sorted(kept)
    local.path("", damaged).write_bytes(b"changed on disk")
    local.path("", gone).unlink()
    first = artifacts.migrate(limit=1)
    assert (first["moved"], first["remaining"]) == (1, 1)
    moved = artifacts.migrate()
    assert (moved["moved"], moved["missing"], moved["mismatched"]) == (1, 1, 1)
    assert {f["sha256"]: f["fault"] for f in moved["faults"]} == {
        damaged: "local bytes do not match",
        gone: "missing",
    }
    assert locations() == {
        damaged: "local",
        gone: "local",
        **dict.fromkeys(sound, "s3"),
    }
    for sha in sound:
        assert (
            bucket.objects["archive", f"link-lens/blobs/{sha[:2]}/{sha}"] == kept[sha]
        )
        assert store.blob_path(sha).read_bytes() == kept[sha]
        assert store.blob_path(sha).is_relative_to(tmp_path / "cache")
        assert local.path("", sha).read_bytes() == kept[sha]  # nothing local is deleted
    again = artifacts.migrate()
    assert (again["moved"], again["missing"], again["mismatched"]) == (0, 1, 1)

    blocked = CliRunner().invoke(cli, ["artifacts", "migrate"])
    assert blocked.exit_code == 3 and json.loads(blocked.stdout)["missing"] == 1
    # Only the location of an artifact may change.
    with pytest.raises(DBAPIError, match="only uri may change"):
        with store.engine().begin() as connection:
            connection.execute(text("UPDATE catalog.artifact SET name = 'renamed'"))


def test_a_release_digest_is_the_same_wherever_the_release_is_served(released):  # noqa: F811
    first = releases.digest()
    assert (first["release_id"], first["profiles"], first["pages"]) == (1, 50, 311)
    assert first == releases.digest(1) and len(first["digest"]) == 64
    shown = json.loads(CliRunner().invoke(cli, ["release", "digest"]).stdout)
    assert shown["digest"] == first["digest"]
    # Another release of the same batch has the same profiles and pages.
    releases.create(released["batch_id"], "test reviewer")
    assert releases.digest(2)["digest"] == first["digest"]
    assert releases.digest(1)["digest"] == first["digest"]


def contract(name, current):
    """Compare a published contract with the code, or write it when asked to."""
    path = CONTRACTS / name
    rendered = json.dumps(current, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if os.environ.get("UPDATE_CONTRACTS"):
        path.write_text(rendered)
    assert path.read_text() == rendered, (
        f"{path} differs from the code. If the change is meant, run "
        "UPDATE_CONTRACTS=1 uv run pytest tests/test_production.py and commit the file."
    )


def test_the_published_rest_contract_matches_the_code():
    contract("openapi.json", app.openapi())


def test_the_published_mcp_tools_match_the_code():
    tools = [
        tool.definition().model_dump(by_alias=True, exclude_none=True)
        | {"toolset": tool.toolset}
        for tool in mcp_server.TOOLS
    ]
    contract(
        "mcp-tools.json", {"instructions": mcp_server.INSTRUCTIONS, "tools": tools}
    )
