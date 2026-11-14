"""Contract tests for the product service: access, limits, every REST route."""

import json
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from link_lens import releases, store
from link_lens.cli import app as cli
from link_lens.db import evidence
from link_lens.db.records import same
from link_lens.okf import render, tree
from link_lens.pipeline import assemble
from link_lens.product import Problem, auth, db, keys, limits, models, queries
from link_lens.product.app import app
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_identity_ops import assembled
from typer.testing import CliRunner

PROBLEM = "application/problem+json"


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    """A fresh rate limiter on a clock the test controls, and no cached concepts."""
    clock = Clock()
    monkeypatch.setattr(limits, "limiter", limits.RateLimiter(clock))
    queries._concepts.clear()
    return clock


@pytest.fixture
def released(spec, snapshot, clock):
    batch = assemble(assembled(spec, snapshot))
    return releases.create(batch["id"], "test reviewer")


@pytest.fixture
def api():
    return TestClient(app)


def key_for(tier="standard", **limits_):
    """A tier, a client on it and a key; returns the request headers and the key."""
    options = {"rate_per_minute": 600, "interfaces": ("rest", "mcp"), **limits_}
    keys.set_tier(tier, **options)
    client = keys.create_client(f"client of {tier}", tier)
    created = keys.create_key(client["client_id"], label="test")
    return {"Authorization": "Bearer " + created["key"]}, created


@pytest.fixture
def headers(released):
    return key_for()[0]


def test_a_key_is_shown_once_and_only_its_hash_is_stored(clock):
    _, created = key_for()
    prefix, secret = keys.parse(created["key"])
    assert created["key"] == f"ll_{prefix}_{secret}" and len(secret) == 64
    with store.engine().connect() as connection:
        row = connection.execute(text("SELECT * FROM access.api_key")).mappings().one()
        stored = connection.execute(
            text("SELECT sha256_hex(key_hash) FROM access.api_key")
        ).scalar_one()
    assert row["prefix"] == prefix and stored == keys.digest(secret) != secret
    assert secret not in json.dumps({k: str(v) for k, v in row.items()})
    assert keys.matches(secret, stored) and not keys.matches(secret + "0", stored)
    for malformed in (
        "",
        "ll_only",
        "xx_" + prefix + "_" + secret,
        f"ll_{prefix}_short",
        None,
    ):
        assert keys.parse(malformed) is None
    first = keys.revoke_key(prefix)
    assert (
        keys.revoke_key(prefix)["revoked_at"] == first["revoked_at"]
    )  # the first time stands
    with pytest.raises(KeyError):
        keys.revoke_key("unknown")
    with pytest.raises(KeyError):
        keys.create_client("nobody", "no-such-tier")
    with pytest.raises(ValueError, match="Unknown interface"):
        keys.set_tier("bad", 1, interfaces=("telnet",))


def test_credentials_are_required_and_checked(released, api):
    headers, created = key_for()
    assert api.get("/health").json() == {"status": "ok"}
    assert "/v1/entities" in api.get("/openapi.json").json()["paths"]
    prefix, secret = keys.parse(created["key"])
    for bad in (
        {},
        {"Authorization": created["key"]},
        {"Authorization": "Basic " + created["key"]},
        {"Authorization": "Bearer not-a-key"},
        {"Authorization": f"Bearer ll_{prefix}_{'0' * 64}"},
        {"Authorization": f"Bearer ll_ffffffffffff_{secret}"},
    ):
        refused = api.get("/v1/sources", headers=bad)
        assert refused.status_code == 401 and refused.headers["content-type"] == PROBLEM
        assert refused.headers["www-authenticate"] == "Bearer"
        assert refused.json()["status"] == 401 and secret not in refused.text
    assert api.get("/v1/sources", headers=headers).status_code == 200

    with store.engine().begin() as connection:
        connection.execute(
            text("UPDATE access.api_key SET expires_at = now() - interval '1 second'")
        )
    assert api.get("/v1/sources", headers=headers).status_code == 401
    with store.engine().begin() as connection:
        connection.execute(
            text("UPDATE access.api_key SET expires_at = now() + interval '1 day'")
        )
    assert api.get("/v1/sources", headers=headers).status_code == 200
    keys.set_client_status(created["client_id"], "suspended")
    assert api.get("/v1/sources", headers=headers).status_code == 401
    keys.set_client_status(created["client_id"], "active")
    keys.revoke_key(created["prefix"])
    assert (
        api.get("/v1/sources", headers=headers).json()["title"] == "Invalid credentials"
    )

    mcp_only, _ = key_for("mcp-only", interfaces=("mcp",))
    refused = api.get("/v1/sources", headers=mcp_only)
    assert (
        refused.status_code == 403
        and "does not include rest" in refused.json()["detail"]
    )


def test_entities_are_searched_and_paged(released, api, headers):
    first = api.get("/v1/entities", headers=headers, params={"limit": 20})
    assert first.status_code == 200 and first.headers["x-linklens-release"] == "1"
    body = first.json()
    assert len(body["entities"]) == 20 and body["next_cursor"]
    seen = [e["entity_id"] for e in body["entities"]]
    while body["next_cursor"]:
        body = api.get(
            "/v1/entities",
            headers=headers,
            params={"limit": 20, "cursor": body["next_cursor"]},
        ).json()
        seen += [e["entity_id"] for e in body["entities"]]
    assert len(seen) == 50 and seen == sorted(set(seen))

    named = api.get(
        "/v1/entities", headers=headers, params={"name": "entity 4"}
    ).json()["entities"]
    assert sorted(e["display_name"] for e in named) == sorted(
        ["Synthetic Entity 4"] + [f"Synthetic Entity {n}" for n in range(40, 50)]
    )
    one = named[0]
    assert set(one) == {
        "entity_id",
        "display_name",
        "identifiers",
        "status",
        "profile_version",
        "okf_path",
    }
    abn = one["identifiers"]["entity.abn"]
    spaced = f"{abn[:2]} {abn[2:5]} {abn[5:]}"
    by_abn = api.get("/v1/entities", headers=headers, params={"abn": spaced}).json()[
        "entities"
    ]
    assert [e["entity_id"] for e in by_abn] == [one["entity_id"]]
    for nothing in (
        {"abn": "00000000000"},
        {"acn": abn},
        {"state": "NSW"},
        {"type": "Trust"},
        {"name": "100%"},
    ):
        assert (
            api.get("/v1/entities", headers=headers, params=nothing).json()["entities"]
            == []
        )

    bad = api.get("/v1/entities", headers=headers, params={"cursor": "%%%"})
    assert bad.status_code == 400 and bad.headers["content-type"] == PROBLEM
    over = api.get("/v1/entities", headers=headers, params={"limit": 5000})
    assert over.status_code == 422 and "limit" in over.json()["detail"]
    assert api.get("/v1/nothing", headers=headers).json()["status"] == 404


def test_entity_and_profile_match_what_is_stored(released, api, headers):
    stored = {
        p["canonical_entity_key"]: p
        for p in store.listing("profiles", owner=released["batch_id"])
    }
    assert len(stored) == 50
    for entity_id, profile in stored.items():
        answer = api.get(f"/v1/entities/{entity_id}/profile", headers=headers)
        assert answer.status_code == 200
        body = answer.json()
        assert answer.headers["etag"] == f'"{profile["profile_version"]}"'
        assert body["profile_version"] == profile["profile_version"]
        assert (
            body["status"] == profile["status"]
            and body["uncertainties"] == profile["uncertainties"]
        )
        assert [f["concept"] for f in body["fields"]] == list(profile["fields"])
        for field in body["fields"]:
            original = profile["fields"][field["concept"]]
            # The same values, statuses and provenance IDs as the stored profile.
            assert (field["value"], field["status"]) == (
                original["value"],
                original["status"],
            )
            assert same(field["provenance"], original["provenance"])
            assert same(field["alternatives"], original["alternatives"])
            assert field["confidence_kind"] == "uncalibrated mapping/source judgements"
            assert (
                field["observation"]["observation_id"]
                == original["provenance"][0]["id"]
            )
            assert field["decision"] == original["decision"]
        assert body["source_records"] == profile["source_records"]

    entity_id = next(iter(stored))
    entity = api.get(f"/v1/entities/{entity_id}", headers=headers).json()
    assert entity["okf_path"] == render.entity_path(entity_id)
    assert entity["profile_version"] == stored[entity_id]["profile_version"]
    etag = f'"{entity["profile_version"]}"'
    unchanged = api.get(
        f"/v1/entities/{entity_id}/profile", headers={**headers, "If-None-Match": etag}
    )
    assert (
        unchanged.status_code == 304
        and unchanged.headers["etag"] == etag
        and not unchanged.content
    )

    with store.engine().connect() as connection:
        page = tree.read(connection, 1, entity["okf_path"])["text"]
    for route in (f"/v1/entities/{entity_id}", f"/v1/entities/{entity_id}/profile"):
        markdown = api.get(route, headers={**headers, "Accept": "text/markdown"})
        assert markdown.headers["content-type"].startswith("text/markdown")
        assert markdown.text == page and markdown.headers["x-linklens-release"] == "1"
    for route in ("", "/profile", "/observations", "/links"):
        missing = api.get(f"/v1/entities/no-such-entity{route}", headers=headers)
        assert missing.status_code == 404 and missing.headers["content-type"] == PROBLEM


def test_observations_evidence_and_links_carry_their_provenance(released, api, headers):
    entity_id = api.get("/v1/entities", headers=headers, params={"limit": 1}).json()[
        "entities"
    ][0]["entity_id"]
    listed = api.get(f"/v1/entities/{entity_id}/observations", headers=headers).json()
    assert len(listed["observations"]) == 4 and listed["next_cursor"] is None
    for observation in listed["observations"]:
        assert (
            observation["entity_id"] == entity_id and observation["licence"] == "CC BY"
        )
        assert (
            observation["timestamp_basis"] == "snapshot"
            and observation["timezone_assumed"] is False
        )
        assert (
            observation["confidence_kind"] == "uncalibrated mapping/source judgements"
        )
        assert observation["observed_at"] and observation["ingested_at"]
    route = f"/v1/entities/{entity_id}/observations"
    assert {
        o["concept"]
        for o in api.get(
            route, headers=headers, params={"concept": "entity.abn"}
        ).json()["observations"]
    } == {"entity.abn"}
    assert {
        o["source_id"]
        for o in api.get(route, headers=headers, params={"source": "source-b"}).json()[
            "observations"
        ]
    } == {"source-b"}
    page = api.get(route, headers=headers, params={"limit": 3}).json()
    rest = api.get(
        route, headers=headers, params={"limit": 3, "cursor": page["next_cursor"]}
    ).json()
    assert [
        o["observation_id"] for o in page["observations"] + rest["observations"]
    ] == [o["observation_id"] for o in listed["observations"]]

    chosen = listed["observations"][0]
    proof = api.get(
        f"/v1/observations/{chosen['observation_id']}", headers=headers
    ).json()
    assert proof["observation"] == chosen and proof["licence"] == "CC BY"
    assert (
        proof["record"]["record_id"] == chosen["record_id"]
        and proof["record"]["row_no"] >= 20
    )
    assert (
        proof["record"]["locator"]["sheet"] == "csv"
        and proof["source"]["title"] == "Fixture"
    )
    assert proof["snapshot"]["observed_at_basis"] == "publication proxy"
    assert proof["snapshot"]["retrieved_at"].startswith("2025-02-01")
    for unknown in ("ab" * 32, "not-an-id"):
        assert (
            api.get(f"/v1/observations/{unknown}", headers=headers).status_code == 404
        )

    links = api.get(f"/v1/entities/{entity_id}/links", headers=headers).json()
    assert len(links) == 1 and links[0]["status"] == "proposed_unreviewed"
    assert (
        "uncalibrated" in links[0]["score_kind"]
        and links[0]["rule"] == "exact_validated_identifier"
    )
    assert {r["source_id"] for r in links[0]["records"]} == {"source-a", "source-b"}


def test_sources_concepts_releases_and_okf(released, api, headers):
    sources = api.get("/v1/sources", headers=headers).json()
    assert [s["source_id"] for s in sources] == ["source-a", "source-b"]
    assert all(
        s["licence"] == "CC BY" and s["okf_path"] == f"/sources/{s['source_id']}.md"
        for s in sources
    )
    assert api.get("/v1/sources/source-a", headers=headers).json() == sources[0]
    assert api.get("/v1/sources/unknown", headers=headers).status_code == 404

    concepts = api.get("/v1/ontology/concepts", headers=headers).json()
    assert len(concepts) == 59 and concepts[0]["name"] == "entity.legal_name"
    address = api.get(
        "/v1/ontology/concepts", headers=headers, params={"scope": "address"}
    ).json()
    assert address and {c["scope"] for c in address} == {"address"}
    state = next(c for c in concepts if c["name"] == "address.state")
    assert state["datatype"] == "enum" and "NSW" in state["allowed_values"]

    listed = api.get("/v1/releases", headers=headers).json()
    assert [(r["release_id"], r["is_current"]) for r in listed] == [(1, True)]
    assert api.get("/v1/releases/current", headers=headers).json() == listed[0]
    assert listed[0]["ontology_hash"] == released["ontology_hash"]

    root = api.get("/v1/okf", headers=headers).json()
    assert [e["name"] for e in root["entries"]] == [
        "entities/",
        "evidence/",
        "index.md",
        "ontology/",
        "sources/",
    ]
    assert root["index"] == "/index.md"
    folder = api.get("/v1/okf/entities/by-source", headers=headers).json()
    assert [e["name"] for e in folder["entries"]] == [
        "index.md",
        "source-a/",
        "source-b/",
    ]
    paged = api.get("/v1/okf/evidence", headers=headers, params={"limit": 2}).json()
    assert len(paged["entries"]) == 2 and paged["next_cursor"]
    index = api.get("/v1/okf/index.md", headers=headers)
    assert (
        index.headers["content-type"].startswith("text/markdown")
        and "# Link Lens" in index.text
    )
    concept = api.get("/v1/okf/ontology/entity/entity.abn.md", headers=headers)
    assert concept.text.startswith("---\ntype: Ontology Concept\n")
    for missing in ("/v1/okf/nowhere", "/v1/okf/entities/zz/none.md"):
        assert api.get(missing, headers=headers).status_code == 404


def test_a_scoped_key_cannot_reach_other_sources_by_any_route(released, api, headers):
    scoped, _ = key_for("scoped", source_scope=["source-a"])
    assert [s["source_id"] for s in api.get("/v1/sources", headers=scoped).json()] == [
        "source-a"
    ]
    assert api.get("/v1/sources/source-b", headers=scoped).status_code == 404
    entity_id = api.get("/v1/entities", headers=scoped, params={"limit": 1}).json()[
        "entities"
    ][0]["entity_id"]
    route = f"/v1/entities/{entity_id}/observations"
    everything = api.get(route, headers=headers).json()["observations"]
    visible = api.get(route, headers=scoped).json()["observations"]
    assert {o["source_id"] for o in everything} == {"source-a", "source-b"}
    assert {o["source_id"] for o in visible} == {"source-a"}
    assert (
        api.get(route, headers=scoped, params={"source": "source-b"}).json()[
            "observations"
        ]
        == []
    )
    hidden = next(o for o in everything if o["source_id"] == "source-b")
    shown = next(o for o in everything if o["source_id"] == "source-a")
    assert (
        api.get(
            f"/v1/observations/{hidden['observation_id']}", headers=scoped
        ).status_code
        == 404
    )
    assert (
        api.get(
            f"/v1/observations/{shown['observation_id']}", headers=scoped
        ).status_code
        == 200
    )

    assert (
        api.get(
            f"/v1/okf{render.evidence_path(hidden['observation_id'])}", headers=scoped
        ).status_code
        == 404
    )
    assert (
        api.get(
            f"/v1/okf{render.evidence_path(shown['observation_id'])}", headers=scoped
        ).status_code
        == 200
    )
    assert api.get("/v1/okf/sources/source-b.md", headers=scoped).status_code == 404
    assert [
        e["name"] for e in api.get("/v1/okf/sources", headers=scoped).json()["entries"]
    ] == [
        "index.md",
        "source-a.md",
    ]
    assert "source-b" not in api.get("/v1/okf/sources/index.md", headers=scoped).text
    assert [
        e["name"]
        for e in api.get("/v1/okf/entities/by-source", headers=scoped).json()["entries"]
    ] == [
        "index.md",
        "source-a/",
    ]
    # A profile is one answer about one entity and is returned whole, with the
    # provenance of every field. Scope limits what can be pulled per source.
    profile = api.get(f"/v1/entities/{entity_id}/profile", headers=scoped).json()
    assert all(field["provenance"] for field in profile["fields"])
    nobody, _ = key_for("no-sources", source_scope=[])
    assert api.get("/v1/sources", headers=nobody).json() == []
    assert api.get(route, headers=nobody).json()["observations"] == []


def test_release_lag_and_history_depth_decide_which_release_answers(
    released, api, clock
):
    runs = store.require("batches", released["batch_id"])["run_ids"]
    for reviewer in ("second", "third"):
        releases.create(assemble(runs)["id"], reviewer)
    latest, _ = key_for("latest")
    assert api.get("/v1/releases/current", headers=latest).json()["release_id"] == 3
    assert [
        r["release_id"] for r in api.get("/v1/releases", headers=latest).json()
    ] == [3, 2, 1]
    assert (
        api.get("/v1/sources", headers=latest, params={"release": 1}).headers[
            "x-linklens-release"
        ]
        == "1"
    )

    lagging, _ = key_for("lagging", release_lag=1)
    current = api.get("/v1/entities", headers=lagging, params={"limit": 1})
    assert current.headers["x-linklens-release"] == "2"
    assert [
        r["release_id"] for r in api.get("/v1/releases", headers=lagging).json()
    ] == [2, 1]
    ahead = api.get("/v1/entities", headers=lagging, params={"release": 3})
    assert ahead.status_code == 404 and "not visible" in ahead.json()["detail"]

    shallow, _ = key_for("current-only", history_depth=1)
    assert [
        r["release_id"] for r in api.get("/v1/releases", headers=shallow).json()
    ] == [3]
    assert (
        api.get("/v1/sources", headers=shallow, params={"release": 2}).status_code
        == 404
    )
    both, _ = key_for("lag-and-depth", release_lag=1, history_depth=2)
    assert [r["release_id"] for r in api.get("/v1/releases", headers=both).json()] == [
        2,
        1,
    ]
    assert (
        api.get("/v1/sources", headers=both, params={"release": 99}).status_code == 404
    )
    behind, _ = key_for("too-far-behind", release_lag=5)
    nothing = api.get("/v1/sources", headers=behind)
    assert (
        nothing.status_code == 404 and nothing.json()["title"] == "No release available"
    )


def test_rate_limit_refills_and_monthly_quota_holds(released, api, clock):
    quick, _ = key_for("two-a-minute", rate_per_minute=2)
    assert [api.get("/v1/sources", headers=quick).status_code for _ in range(3)] == [
        200,
        200,
        429,
    ]
    limited = api.get("/v1/sources", headers=quick)
    assert (
        limited.headers["content-type"] == PROBLEM
        and limited.json()["title"] == "Rate limit reached"
    )
    assert limited.headers["retry-after"] == "30"
    clock.now += 30
    assert api.get("/v1/sources", headers=quick).status_code == 200
    assert api.get("/v1/sources", headers=quick).status_code == 429
    other, _ = key_for("another-two", rate_per_minute=2)
    assert (
        api.get("/v1/sources", headers=other).status_code == 200
    )  # each key has its own bucket

    capped, created = key_for("three-a-month", monthly_quota=3)
    codes = [
        api.get(route, headers=capped).status_code
        for route in ("/v1/sources", "/v1/sources/unknown", "/v1/sources")
    ]
    assert codes == [200, 404, 200]  # a call that finds nothing still counts
    over = api.get("/v1/sources", headers=capped)
    assert over.status_code == 429 and over.json()["title"] == "Monthly quota reached"
    assert 0 < int(over.headers["retry-after"]) <= 31 * 86400
    second = keys.create_key(
        created["client_id"]
    )  # the quota is the client's, not the key's
    assert (
        api.get(
            "/v1/sources", headers={"Authorization": "Bearer " + second["key"]}
        ).status_code
        == 429
    )
    used = keys.usage(created["client_id"])
    assert [(u["interface"], u["calls"], u["prefix"]) for u in used] == [
        ("rest", 3, created["prefix"])
    ]
    assert used[0]["month"] == datetime.now(UTC).strftime("%Y-%m")
    assert (
        limits.seconds_to_next_month(datetime(2026, 12, 31, 23, 59, 30, tzinfo=UTC))
        == 30
    )
    with store.engine().begin() as connection:  # last month's calls do not count
        connection.execute(text("UPDATE access.api_usage SET day = day - 40"))
    assert api.get("/v1/sources", headers=capped).status_code == 200


def test_product_role_reads_serving_and_nothing_in_core(released):
    with db.session() as connection:
        assert (
            connection.execute(text("SELECT current_user")).scalar_one()
            == "linklens_product"
        )
        assert (
            connection.execute(text("SELECT count(*) FROM serving.entity")).scalar_one()
            == 50
        )
        assert (
            connection.execute(text("SELECT count(*) FROM access.tier")).scalar_one()
            == 0
        )
    for forbidden in (
        "SELECT * FROM identity.profile",
        "SELECT * FROM evidence.observation",
        "SELECT * FROM onboarding.run",
        "SELECT * FROM ontology.concept",
        "SELECT * FROM catalog.source",
        "SELECT * FROM ops.release",
        "SELECT * FROM legacy.runs",
        "INSERT INTO access.tier (id, rate_per_minute, interfaces, toolsets) VALUES ('x', 1, '{}', '{}')",
        "UPDATE access.api_key SET revoked_at = NULL",
        "DELETE FROM access.api_usage",
    ):
        with pytest.raises(DBAPIError, match="permission denied"):
            with db.session() as connection:
                connection.execute(text(forbidden))


def test_serving_documents_equal_the_stored_records(released):
    profiles = {
        p["canonical_entity_key"]: p
        for p in store.listing("profiles", owner=released["batch_id"])
    }
    with store.engine().connect() as connection:
        observations = {o["id"]: o for o in evidence.observations(connection)}
    with db.session() as connection:
        served = connection.execute(
            text("SELECT entity_id, document FROM serving.profile WHERE release_id = 1")
        ).all()
        claims = connection.execute(
            text(
                "SELECT observation_id, document FROM serving.observation WHERE release_id = 1"
            )
        ).all()
    assert len(served) == 50 and len(claims) == 200 == len(observations)
    for entity_id, document in served:
        assert same(document, profiles[entity_id]), entity_id
    for observation_id, document in claims:
        assert same(document, observations[observation_id]), observation_id


def test_an_answer_naming_an_unknown_concept_is_refused(released):
    with db.session() as connection:
        names = queries.concept_names(connection, {"release_id": 1})
    field = {
        "concept": "entity.abn",
        "status": "selected",
        "value": "1",
        "values": None,
        "decision": None,
        "temporal_caveat": None,
        "confidence": None,
        "confidence_kind": "uncalibrated",
        "observation": None,
        "provenance": [],
        "alternatives": [],
    }
    assert models.check(models.ProfileField, field, names).concept == "entity.abn"
    with pytest.raises(ValidationError, match="not a concept of this release"):
        models.check(
            models.ProfileField, {**field, "concept": "invented.concept"}, names
        )
    for required in ("status", "provenance", "alternatives", "confidence_kind"):
        with pytest.raises(ValidationError):
            models.check(
                models.ProfileField,
                {k: v for k, v in field.items() if k != required},
                names,
            )
    with pytest.raises(Problem) as refused:
        queries.decode("***")
    assert refused.value.status == 400
    assert auth.RESOLVERS == [auth.api_key]  # the seam for a second kind of credential


def test_cli_manages_tiers_clients_keys_and_usage(released, api):
    runner = CliRunner()
    tier = runner.invoke(
        cli,
        [
            "access",
            "tier",
            "set",
            "starter",
            "--rate-per-minute",
            "60",
            "--monthly-quota",
            "10000",
            "--interface",
            "rest",
            "--source",
            "source-a",
            "--release-lag",
            "0",
            "--history-depth",
            "1",
        ],
    )
    assert tier.exit_code == 0 and json.loads(tier.output)["source_scope"] == [
        "source-a"
    ]
    assert (
        runner.invoke(
            cli,
            [
                "access",
                "tier",
                "set",
                "x",
                "--rate-per-minute",
                "1",
                "--interface",
                "fax",
            ],
        ).exit_code
        == 2
    )
    assert (
        runner.invoke(
            cli, ["access", "client", "create", "Nobody", "--tier", "missing"]
        ).exit_code
        == 2
    )
    client = json.loads(
        runner.invoke(
            cli, ["access", "client", "create", "Acme", "--tier", "starter"]
        ).output
    )
    created = json.loads(
        runner.invoke(
            cli,
            [
                "access",
                "key",
                "create",
                client["client_id"],
                "--label",
                "ci",
                "--expires-in-days",
                "30",
            ],
        ).output
    )
    assert (
        created["key"].startswith("ll_" + created["prefix"] + "_")
        and created["expires_at"]
    )
    headers = {"Authorization": "Bearer " + created["key"]}
    assert [s["source_id"] for s in api.get("/v1/sources", headers=headers).json()] == [
        "source-a"
    ]
    usage = json.loads(
        runner.invoke(
            cli, ["access", "usage", "--client-id", client["client_id"]]
        ).output
    )
    assert [(u["client"], u["calls"], u["tier_id"]) for u in usage] == [
        ("Acme", 1, "starter")
    ]
    assert (
        runner.invoke(cli, ["access", "key", "revoke", created["prefix"]]).exit_code
        == 0
    )
    assert api.get("/v1/sources", headers=headers).status_code == 401
    assert runner.invoke(cli, ["access", "key", "revoke", "unknown"]).exit_code == 2
    assert created["key"] not in runner.invoke(cli, ["access", "usage"]).output


def test_a_numeric_profile_value_is_answered_as_a_number(released, api, headers):
    profile = deepcopy(store.listing("profiles", owner=released["batch_id"])[0])
    entity_id = "entity-with-a-number"
    profile["canonical_entity_key"] = entity_id
    profile["fields"]["entity.abn"]["value"] = 41
    store.put(
        "profiles",
        f"{released['batch_id']}:{entity_id}",
        profile,
        owner=released["batch_id"],
    )

    answer = api.get(f"/v1/entities/{entity_id}/profile", headers=headers).json()
    values = {field["concept"]: field["value"] for field in answer["fields"]}
    assert values["entity.abn"] == 41
    assert values["entity.legal_name"] == profile["fields"]["entity.legal_name"]["value"]

    # Search matches the text of a value, and a number has no text to match.
    found = api.get("/v1/entities", params={"abn": "41"}, headers=headers).json()
    assert entity_id not in [entity["entity_id"] for entity in found["entities"]]
