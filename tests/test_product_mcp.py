"""Contract tests for the MCP interface: toolsets, parity with REST, limits, scope."""

import json
import re
from contextlib import asynccontextmanager

import httpx2
import pytest
from fastapi.testclient import TestClient
from link_lens import store
from link_lens.interfaces import mcp_server
from link_lens.okf import render
from link_lens.product import keys, queries
from link_lens.product.app import app
from mcp import Client, MCPError
from mcp.client.streamable_http import streamable_http_client
from test_product_rest import clock, key_for, released  # noqa: F401

DATA = ["search_entities", "get_profile", "list_observations", "get_evidence"]
DATA += ["describe_concepts"]
FILES = ["okf_ls", "okf_read", "okf_find", "okf_grep"]
URL = "http://product"


def http(headers=None):
    return httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app), headers=headers, base_url=URL
    )


@asynccontextmanager
async def connected(headers, path="/mcp", mode="auto"):
    """An MCP client holding only a URL and a key, against the running app."""
    async with app.router.lifespan_context(app), http(headers) as client:
        transport = streamable_http_client(URL + path, http_client=client)
        async with Client(transport, mode=mode) as session:
            yield session


def both(**limits):
    return key_for("both", toolsets=("data", "files"), **limits)


async def names(session):
    return [tool.name for tool in (await session.list_tools()).tools]


def text_of(result):
    return "".join(part.text for part in result.content)


@pytest.mark.asyncio
async def test_a_key_is_shown_the_toolsets_of_its_tier(released):  # noqa: F811
    headers, _ = both()
    for mode in ("auto", "legacy"):
        async with connected(headers, mode=mode) as session:
            listed = (await session.list_tools()).tools
            assert [tool.name for tool in listed] == DATA + FILES
            for tool in listed:
                # Agents get a description and a closed schema; nothing writes.
                assert len(tool.description) > 80 and tool.annotations.read_only_hint
                assert tool.input_schema["additionalProperties"] is False
    async with connected(headers, "/mcp/data") as session:
        assert await names(session) == DATA
    async with connected(headers, "/mcp/files") as session:
        assert await names(session) == FILES

    data_only, _ = key_for("data-only", toolsets=("data",))
    async with connected(data_only) as session:
        assert await names(session) == DATA
        # A tool outside the tier does not exist for this key.
        with pytest.raises(MCPError, match="Unknown tool: okf_ls"):
            await session.call_tool("okf_ls", {"path": "/"})
        with pytest.raises(MCPError, match="Unknown tool: drop_everything"):
            await session.call_tool("drop_everything", {})
    assert sum(row["calls"] for row in keys.usage()) == 0


@pytest.mark.asyncio
async def test_every_request_needs_a_key_that_includes_mcp(released):  # noqa: F811
    listing = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    accept = {"Accept": "application/json, text/event-stream"}
    data_only, created = key_for("data-only", toolsets=("data",))
    rest_only, _ = key_for("rest-only", interfaces=("rest",), toolsets=("data",))
    async with app.router.lifespan_context(app), http(accept) as client:
        for path in ("/mcp", "/mcp/data", "/mcp/files"):
            refused = await client.post(path, json=listing)
            assert refused.status_code == 401
            assert refused.headers["content-type"] == "application/problem+json"
            assert refused.headers["www-authenticate"] == "Bearer"
            wrong = {"Authorization": "Bearer ll_000000000000_" + "0" * 64}
            assert (
                await client.post(path, json=listing, headers=wrong)
            ).status_code == 401
            assert (await client.get(path)).status_code == 401
        assert (
            await client.post("/mcp", json=listing, headers=rest_only)
        ).status_code == 403
        refused = await client.post("/mcp/files", json=listing, headers=data_only)
        assert refused.status_code == 403
        assert refused.json()["title"] == "Toolset not in tier"
        assert (
            await client.post("/mcp/data", json=listing, headers=data_only)
        ).status_code == 200
        keys.revoke_key(created["prefix"])
        assert (
            await client.post("/mcp/data", json=listing, headers=data_only)
        ).status_code == 401


@pytest.mark.asyncio
async def test_data_tools_answer_what_rest_answers(released):  # noqa: F811
    headers, _ = both()
    rest = TestClient(app)
    stored = {
        p["canonical_entity_key"]: p
        for p in store.listing("profiles", owner=released["batch_id"])
    }
    entity_id, profile = sorted(stored.items())[0]
    abn = profile["fields"]["entity.abn"]["value"]
    async with connected(headers, "/mcp/data") as session:
        found = await session.call_tool("search_entities", {"abn": abn})
        # The text is the same JSON as the structured content.
        assert json.loads(text_of(found)) == found.structured_content
        over_rest = rest.get("/v1/entities", params={"abn": abn}, headers=headers)
        assert found.structured_content == {
            "release": released["release_id"],
            **over_rest.json(),
        }
        entity = found.structured_content["entities"][0]
        assert entity["entity_id"] == entity_id
        assert entity["okf_path"] == render.entity_path(entity_id)

        summary = (
            await session.call_tool("get_profile", {"entity_id": entity_id})
        ).structured_content
        assert summary["profile_version"] == profile["profile_version"]
        assert [claim["concept"] for claim in summary["fields"]] == list(
            profile["fields"]
        )
        for claim in summary["fields"]:
            original = profile["fields"][claim["concept"]]
            assert (claim["value"], claim["status"], claim["decision"]) == (
                original["value"],
                original["status"],
                original["decision"],
            )
            assert [e["observation_id"] for e in claim["evidence"]] == [
                e["id"] for e in original["provenance"]
            ]
            assert all(e["observed_at_basis"] for e in claim["evidence"])
            assert claim["alternatives"] == [] and claim["alternatives_total"] == 0
            assert "uncalibrated" in claim["confidence_kind"]
        assert [s["licence"] for s in summary["sources"]] == ["CC BY", "CC BY"]

        cited = summary["fields"][0]["evidence"][0]["observation_id"]
        evidence = await session.call_tool("get_evidence", {"observation_id": cited})
        over_rest = rest.get(f"/v1/observations/{cited}", headers=headers).json()
        assert evidence.structured_content == {"release": 1, **over_rest}
        assert evidence.structured_content["record"]["locator"]["row"]
        assert evidence.structured_content["licence"] == "CC BY"

        listed = await session.call_tool(
            "list_observations", {"entity_id": entity_id, "concept": "entity.abn"}
        )
        over_rest = rest.get(
            f"/v1/entities/{entity_id}/observations",
            params={"concept": "entity.abn"},
            headers=headers,
        ).json()
        assert listed.structured_content == {"release": 1, **over_rest}
        assert len(over_rest["observations"]) == 2

        scopes = (await session.call_tool("describe_concepts", {})).structured_content
        assert "entity.abn" in next(
            s["concepts"] for s in scopes["scopes"] if s["scope"] == "entity"
        )
        defined = (
            await session.call_tool("describe_concepts", {"scope": "address"})
        ).structured_content["concepts"]
        over_rest = rest.get(
            "/v1/ontology/concepts", params={"scope": "address"}, headers=headers
        ).json()
        assert defined == over_rest and len(defined) > 3

        missing = await session.call_tool("get_profile", {"entity_id": "nobody"})
        assert missing.is_error and "Not found" in text_of(missing)
        assert missing.structured_content["error"]["status"] == 404


@pytest.mark.asyncio
async def test_file_tools_walk_the_same_release(released):  # noqa: F811
    headers, _ = both()
    rest = TestClient(app)
    async with connected(headers) as session:
        root = await session.call_tool("okf_ls", {})
        assert [e["name"] for e in root.structured_content["entries"]] == [
            "entities/",
            "evidence/",
            "index.md",
            "ontology/",
            "sources/",
        ]
        assert "/entities/  (50 entries)" in text_of(root)
        # The evidence folder has no index; it reports the pages beneath it.
        assert "/evidence/  (200 entries)" in text_of(root)
        assert "/index.md" in text_of(root)

        found = await session.call_tool("search_entities", {"limit": 1})
        entity = found.structured_content["entities"][0]
        # A data result names the page, and the page names the entity.
        page = await session.call_tool(
            "okf_read", {"path": entity["okf_path"], "limit": 50}
        )
        markdown = rest.get(
            "/v1/okf" + entity["okf_path"], headers=headers
        ).text.splitlines(keepends=True)
        assert page.structured_content["total_lines"] == len(markdown)
        assert page.structured_content["text"] == "".join(markdown[:50])
        assert f"entity_id: {entity['entity_id']}\n" in text_of(page)
        assert text_of(page).endswith(
            f"[lines 0 to 49 of {len(markdown)}: call again with offset=50]"
        )
        lines, offset = [], 0
        while offset is not None:
            part = await session.call_tool(
                "okf_read", {"path": entity["okf_path"], "offset": offset, "limit": 40}
            )
            lines.append(part.structured_content["text"])
            offset = part.structured_content["next_offset"]
        assert "".join(lines) == "".join(markdown) and len(lines) > 2
        whole = await session.call_tool("okf_read", {"path": entity["okf_path"]})
        assert text_of(whole) == "".join(markdown)

        abn = entity["identifiers"]["entity.abn"]
        matches = await session.call_tool(
            "okf_grep", {"pattern": f"^entity\\.abn: {abn}$", "path": "/entities"}
        )
        assert [m["path"] for m in matches.structured_content["matches"]] == [
            entity["okf_path"]
        ]
        assert text_of(matches) == f"{entity['okf_path']}:6: entity.abn: {abn}"

        evidence = re.search(r"\((\S*/evidence/\S+\.md)\)", "".join(markdown)).group(1)
        evidence = "/evidence" + evidence.split("/evidence")[1]
        claim = await session.call_tool("okf_read", {"path": evidence})
        observation_id = re.search(r"observation_id: (\w+)", text_of(claim)).group(1)
        through_data = await session.call_tool(
            "get_evidence", {"observation_id": observation_id}
        )
        assert (
            through_data.structured_content["observation"]["entity_id"]
            == entity["entity_id"]
        )

        entities = await session.call_tool(
            "okf_find", {"path": "/entities", "type": "Business Profile", "limit": 200}
        )
        assert len(entities.structured_content["pages"]) == 50
        assert entity["okf_path"] in text_of(entities)

        for arguments, title in (
            ({"path": "/entities/nowhere.md"}, "Not found"),
            ({"path": "/../etc/passwd"}, "Not found"),
        ):
            refused = await session.call_tool("okf_read", arguments)
            assert refused.is_error and title in text_of(refused)
        refused = await session.call_tool("okf_grep", {"pattern": "x", "path": "/"})
        assert refused.is_error and "needs a folder" in text_of(refused)
        refused = await session.call_tool(
            "okf_grep", {"pattern": "(", "path": "/entities"}
        )
        assert refused.is_error and "Invalid pattern" in text_of(refused)
        assert (await session.call_tool("okf_ls", {"path": "/nowhere"})).is_error


@pytest.mark.asyncio
async def test_results_are_bounded_and_say_how_to_continue(released):  # noqa: F811
    headers, _ = both()
    async with connected(headers) as session:
        seen, cursor, pages = [], None, 0
        while pages == 0 or cursor:
            arguments = {"cursor": cursor} if cursor else {}
            page = (
                await session.call_tool("search_entities", arguments)
            ).structured_content
            assert len(page["entities"]) <= mcp_server.ENTITIES
            seen += [entity["entity_id"] for entity in page["entities"]]
            cursor, pages = page["next_cursor"], pages + 1
        assert (len(seen), len(set(seen)), pages) == (50, 50, 3)

        lines = await session.call_tool(
            "okf_grep", {"pattern": "^entity\\.", "path": "/entities"}
        )
        assert len(lines.structured_content["matches"]) == mcp_server.MATCHES
        cursor = lines.structured_content["next_cursor"]
        assert text_of(lines).endswith(
            f"[more: call again with cursor={json.dumps(cursor)}]"
        )
        rest_of = await session.call_tool(
            "okf_grep", {"pattern": "^entity\\.", "path": "/entities", "cursor": cursor}
        )
        assert len(rest_of.structured_content["matches"]) == 50
        assert rest_of.structured_content["next_cursor"] is None

        listing = await session.call_tool("okf_ls", {"path": "/evidence", "limit": 3})
        assert len(listing.structured_content["entries"]) == 3
        assert listing.structured_content["next_cursor"]

        for name, arguments, problem in (
            ("search_entities", {"limit": 5000}, "limit: 5000 is greater than"),
            ("okf_read", {"path": "/index.md", "limit": 0}, "limit: 0 is less than"),
            ("okf_read", {}, "'path' is a required property"),
            (
                "get_profile",
                {"entity_id": "x", "sql": "SELECT 1"},
                "Additional properties",
            ),
            ("search_entities", {"cursor": "not a cursor"}, "Invalid cursor"),
        ):
            refused = await session.call_tool(name, arguments)
            assert refused.is_error and problem in text_of(refused), text_of(refused)
            assert refused.structured_content["error"]["status"] == 400


def test_a_page_holds_what_fits_and_points_at_the_rest():
    rows = [{"id": f"{n:02}", "value": "x" * 100} for n in range(10)]
    kept, cursor = queries.page(rows, 9, lambda row: row["id"], budget=400)
    assert [row["id"] for row in kept] == ["00", "01", "02"]
    assert queries.decode(cursor) == "02"
    # A row larger than the whole budget is still answered, alone.
    kept, cursor = queries.page(rows, 9, lambda row: row["id"], budget=10)
    assert [row["id"] for row in kept] == ["00"] and queries.decode(cursor) == "00"
    kept, cursor = queries.page(rows[:3], 9, lambda row: row["id"], budget=10_000)
    assert len(kept) == 3 and cursor is None


def test_a_claim_with_many_values_lists_the_first_and_counts_the_rest():
    def stated(number):
        return {
            "value": f"condition {number}",
            "confidence": {"field_confidence": 0.9},
            "provenance": [{"id": f"{number:064x}", "source_id": "source-a"}],
        }

    claim = queries.claim(
        "licence.authorisation_condition",
        {"status": "multiple_values", "values": [stated(n) for n in range(56)]},
    )
    assert (len(claim["values"]), claim["values_total"]) == (queries.SHOWN, 56)
    assert claim["values"][0]["evidence"][0]["observation_id"] == f"{0:064x}"
    unresolved = queries.claim(
        "entity.legal_name",
        {"status": "unresolved", "alternatives": [stated(1), stated(2)]},
    )
    assert unresolved["value"] is None and unresolved["alternatives_total"] == 2
    assert [a["value"] for a in unresolved["alternatives"]] == [
        "condition 1",
        "condition 2",
    ]


@pytest.mark.asyncio
async def test_tool_calls_are_counted_and_limited_as_mcp(released, clock):  # noqa: F811
    headers, created = both(rate_per_minute=3, monthly_quota=5)
    rest = TestClient(app)
    async with connected(headers) as session:
        await session.list_tools()
        assert keys.usage() == []
        for _ in range(3):
            assert not (await session.call_tool("okf_ls", {})).is_error
        limited = await session.call_tool("okf_ls", {})
        assert limited.is_error and "Rate limit reached" in text_of(limited)
        assert limited.structured_content["error"] == {
            "status": 429,
            "title": "Rate limit reached",
            "detail": "This tier allows 3 calls a minute.",
            "retry_after_seconds": 20,
        }
        assert "Retry after 20 seconds." in text_of(limited)
        used = {(row["prefix"], row["interface"]): row["calls"] for row in keys.usage()}
        assert used == {(created["prefix"], "mcp"): 3}

        # The monthly quota is the client's, whichever interface it calls.
        clock.now += 60
        assert rest.get("/v1/sources", headers=headers).status_code == 200
        refused = await session.call_tool("get_profile", {"entity_id": "missing"})
        assert refused.structured_content["error"]["status"] == 404
        spent = await session.call_tool("okf_ls", {})
        assert spent.structured_content["error"]["title"] == "Monthly quota reached"
        assert rest.get("/v1/sources", headers=headers).status_code == 429
        used = {row["interface"]: row["calls"] for row in keys.usage()}
        assert used == {"mcp": 4, "rest": 1}


@pytest.mark.asyncio
async def test_a_scoped_key_stays_in_scope_over_mcp(released):  # noqa: F811
    everything, _ = both()
    scoped, _ = key_for("scoped", toolsets=("data", "files"), source_scope=["source-a"])
    async with connected(everything) as session:
        entity = (
            await session.call_tool("search_entities", {"limit": 1})
        ).structured_content["entities"][0]
        claims = (
            await session.call_tool(
                "list_observations", {"entity_id": entity["entity_id"]}
            )
        ).structured_content["observations"]
        assert {claim["source_id"] for claim in claims} == {"source-a", "source-b"}
        hidden = next(
            c["observation_id"] for c in claims if c["source_id"] == "source-b"
        )
        shown = next(
            c["observation_id"] for c in claims if c["source_id"] == "source-a"
        )
    async with connected(scoped) as session:
        claims = (
            await session.call_tool(
                "list_observations", {"entity_id": entity["entity_id"]}
            )
        ).structured_content["observations"]
        assert {claim["source_id"] for claim in claims} == {"source-a"}
        for name, arguments in (
            ("get_evidence", {"observation_id": hidden}),
            ("okf_read", {"path": render.evidence_path(hidden)}),
            ("okf_read", {"path": "/sources/source-b.md"}),
        ):
            refused = await session.call_tool(name, arguments)
            assert (
                refused.is_error
                and refused.structured_content["error"]["status"] == 404
            )
        for name, arguments in (
            ("get_evidence", {"observation_id": shown}),
            ("okf_read", {"path": render.evidence_path(shown)}),
        ):
            assert not (await session.call_tool(name, arguments)).is_error
        found = await session.call_tool(
            "okf_grep", {"pattern": "^source: ", "path": "/evidence", "limit": 200}
        )
        assert {m["line"] for m in found.structured_content["matches"]} == {
            "source: source-a"
        }
        pages = await session.call_tool("okf_find", {"path": "/sources"})
        assert [p["path"] for p in pages.structured_content["pages"]] == [
            "/sources/source-a.md"
        ]
        # A profile is answered whole; the title of the other source is not given.
        summary = (
            await session.call_tool("get_profile", {"entity_id": entity["entity_id"]})
        ).structured_content
        assert [
            (s["source_id"], s["title"], s["licence"]) for s in summary["sources"]
        ] == [
            ("source-a", "Fixture", "CC BY"),
            ("source-b", None, "CC BY"),
        ]


@pytest.mark.asyncio
async def test_the_fixed_tasks_can_be_done_with_either_toolset(released):  # noqa: F811
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / "scripts" / "mcp_agent_eval.py"
    spec = importlib.util.spec_from_file_location("mcp_agent_eval", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    headers, created = both()

    @asynccontextmanager
    async def connect(path):
        async with http(headers) as client:
            transport = streamable_http_client(URL + path, http_client=client)
            async with Client(transport) as session:
                yield session

    async with app.router.lifespan_context(app):
        record = await script.evaluate(connect)
    failed = [task for task in record["tasks"] if not task["agree"]]
    assert not failed, json.dumps(failed, indent=1)[:3000]
    assert record["tools"] == {"data": sorted(DATA), "files": sorted(FILES)}
    assert record["summary"]["tasks"] == 10 and record["summary"]["agreed"] == 10
    # Every call of the run is in the usage of the key, under mcp.
    calls = record["summary"]["calls"]
    used = {(row["prefix"], row["interface"]): row["calls"] for row in keys.usage()}
    assert used == {(created["prefix"], "mcp"): calls["data"] + calls["files"] + 1}
