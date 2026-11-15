"""Release bundles, their download links and the per-entity viewer."""

import hashlib
import io
import json
import tarfile
import time

import pytest
from fastapi.testclient import TestClient
from link_lens import bundles, releases, store
from link_lens.cli import app as cli
from link_lens.okf import bundle as tree_files
from link_lens.okf import render, tree
from link_lens.pipeline import assemble
from link_lens.product import db, keys, queries
from link_lens.product import links as download
from link_lens.product.app import app
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_identity_ops import assembled
from test_product_rest import clock, key_for  # noqa: F401
from typer.testing import CliRunner


@pytest.fixture
def batch(spec, snapshot):
    return assemble(assembled(spec, snapshot))


def entities_of(batch):
    return sorted(
        p["canonical_entity_key"] for p in store.listing("profiles", owner=batch["id"])
    )


def unpack(sha):
    """The files of a stored bundle, by path."""
    data = store.blob_path(sha).read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        return {m.name: tar.extractfile(m).read() for m in tar.getmembers()}


def graph(html):
    """The nodes and edges a viewer page draws."""
    line = next(
        line for line in html.splitlines() if line.startswith("window.BUNDLE =")
    )
    data = json.loads(line.removeprefix("window.BUNDLE = ").rstrip(";"))
    nodes = {node["data"]["id"] for node in data["nodes"]}
    edges = {(e["data"]["source"], e["data"]["target"]) for e in data["edges"]}
    return nodes, edges


def test_a_scope_is_a_named_bounded_list_set_by_a_person(batch):
    some = entities_of(batch)[:3]
    scope = bundles.set_scope("demo", some + some[:1], "owner")
    assert (scope["entity_ids"], scope["on_release"], scope["set_by"]) == (
        some,
        True,
        "owner",
    )
    assert bundles.set_scope("demo", some[:2], "owner")["entity_ids"] == some[:2]
    assert [s["name"] for s in bundles.scopes()] == ["demo"]
    for name, ids, reviewer in (
        ("demo", [], "owner"),
        ("demo", some, " "),
        ("demo", [str(n) for n in range(bundles.LIMIT + 1)], "owner"),
    ):
        with pytest.raises(ValueError):
            bundles.set_scope(name, ids, reviewer)
    with pytest.raises(DBAPIError, match="bundle_scope_name_check"):
        bundles.set_scope("Not A Name", some, "owner")

    runner = CliRunner()
    made = runner.invoke(
        cli,
        ["release", "scope", "set", "sample", "--reviewer", "owner", "--manual"]
        + [part for entity in some for part in ("--entity", entity)],
    )
    assert made.exit_code == 0 and json.loads(made.stdout)["on_release"] is False
    listed = json.loads(runner.invoke(cli, ["release", "scope", "list"]).stdout)
    assert [s["name"] for s in listed] == ["demo", "sample"]
    assert (
        runner.invoke(
            cli, ["release", "scope", "set", "x", "--reviewer", "o"]
        ).exit_code
        == 2
    )


def test_creating_a_release_builds_the_demo_bundle_without_a_command(batch):
    chosen = entities_of(batch)[:3]
    bundles.set_scope("demo", chosen + ["not-in-this-release"], "owner")
    bundles.set_scope("by-hand", chosen[:1], "owner", on_release=False)

    release = releases.create(batch["id"], "test reviewer")
    (built,) = release["bundles"]
    assert (built["scope"], built["created"], built["entity_count"]) == (
        "demo",
        True,
        3,
    )
    assert built["client_id"] is None and built["source_scope"] is None

    files = unpack(built["artifact_sha"])
    listed = json.loads(files["manifest.json"])
    assert hashlib.sha256(files["manifest.json"]).hexdigest() == built["manifest_sha"]
    assert (listed["release_id"], listed["scope"], listed["entities"]) == (1, "demo", 3)
    # The manifest names every other file with its hash.
    assert {f["path"] for f in listed["files"]} == set(files) - {"manifest.json"}
    assert built["file_count"] == len(files)
    for entry in listed["files"]:
        assert hashlib.sha256(files[entry["path"]]).hexdigest() == entry["sha256"]
        assert len(files[entry["path"]]) == entry["size"]

    # A page in the bundle is the bytes the tree returns for its path.
    with store.engine().connect() as connection:
        pages = [name for name in files if name.endswith(".md")]
        compared = 0
        for name in pages:
            if name.endswith("index.md"):
                continue  # an index of a subset lists only the subset
            assert files[name].decode() == tree.read(connection, 1, "/" + name)["text"]
            compared += 1
    entity_pages = [n for n in pages if n.startswith("entities/") and "/by-" not in n]
    entity_pages = [n for n in entity_pages if not n.endswith("index.md")]
    assert sorted(entity_pages) == sorted(render.entity_path(e)[1:] for e in chosen)
    assert sum(name.startswith("evidence/") for name in pages) == 3 * 4
    assert {n for n in pages if n.startswith("sources/") and "index" not in n} == {
        "sources/source-a.md",
        "sources/source-b.md",
    }
    assert compared == 3 + 12 + 2 + sum(n.startswith("ontology/") for n in pages) - sum(
        n.startswith("ontology/") and n.endswith("index.md") for n in pages
    )
    # The viewer is the vendored one, with its licence header kept.
    assert "index.md" in files and files["viewer.html"].startswith(b"<!DOCTYPE html>")
    assert (
        b"Licensed under the Apache License, Version 2.0" in files["viewer.html"][:400]
    )
    nodes, edges = graph(files["viewer.html"].decode())
    assert len([n for n in nodes if n.startswith("entities/")]) == 3

    # Building it again makes the same archive and adds nothing.
    again = bundles.build(1, "demo")
    assert (again["created"], again["artifact_sha"], again["id"]) == (
        False,
        built["artifact_sha"],
        built["id"],
    )
    assert [b["scope"] for b in bundles.listing(1)] == ["demo"]
    # A scope that changed gets a new bundle; the old one stays.
    bundles.set_scope("demo", chosen[:2], "owner")
    changed = bundles.build(1, "demo")
    assert changed["created"] and changed["manifest_sha"] != built["manifest_sha"]
    assert [b["entity_count"] for b in bundles.listing(1)] == [2, 3]
    with pytest.raises(DBAPIError, match="append-only|forbid|cannot be updated"):
        with store.engine().begin() as connection:
            connection.execute(text("UPDATE ops.release_bundle SET entity_count = 0"))

    runner = CliRunner()
    by_hand = runner.invoke(cli, ["release", "bundle", "--scope", "by-hand"])
    assert by_hand.exit_code == 0 and json.loads(by_hand.stdout)["entity_count"] == 1
    assert len(json.loads(runner.invoke(cli, ["release", "bundles"]).stdout)) == 3
    assert (
        runner.invoke(cli, ["release", "bundle", "--scope", "nothing"]).exit_code == 2
    )


def test_a_bundle_that_fails_does_not_undo_the_release(batch, monkeypatch):
    bundles.set_scope("demo", entities_of(batch)[:1], "owner")

    def broken(*arguments, **options):
        raise ValueError("no viewer today")

    monkeypatch.setattr(bundles, "viewer", broken)
    release = releases.create(batch["id"], "test reviewer")
    assert release["release_id"] == 1
    assert release["bundles"] == [{"scope": "demo", "error": "no viewer today"}]
    assert releases.show(1)["release_id"] == 1 and bundles.listing(1) == []


def test_a_client_bundle_holds_what_the_client_may_see(batch, tmp_path):
    releases.create(batch["id"], "test reviewer")
    keys.set_tier("all", rate_per_minute=60, interfaces=("rest",))
    keys.set_tier(
        "one", rate_per_minute=60, interfaces=("rest",), source_scope=["source-a"]
    )
    everything = keys.create_client("sees everything", "all")["client_id"]
    scoped = keys.create_client("sees one source", "one")["client_id"]

    whole = bundles.build(1, f"client:{everything}")
    written = tree_files.write(1, tmp_path / "tree")
    files = unpack(whole["artifact_sha"])
    assert whole["client_id"] == everything and whole["source_scope"] is None
    assert whole["entity_count"] == 50 and whole["withheld_links"] == 0
    assert len(files) == written["files"] + 2  # the viewer and the manifest
    for path in (tmp_path / "tree").rglob("*.md"):
        assert (
            files[path.relative_to(tmp_path / "tree").as_posix()] == path.read_bytes()
        )

    part = bundles.build(1, f"client:{scoped}")
    files = unpack(part["artifact_sha"])
    assert part["source_scope"] == ["source-a"] and part["entity_count"] == 50
    assert "sources/source-a.md" in files and "sources/source-b.md" not in files
    assert sum(name.startswith("evidence/") for name in files) == 100
    for name, body in files.items():
        if name.startswith("evidence/"):
            assert b'"source_id": "source-a"' in body
    # Entity pages are whole, so they still link to the evidence left out.
    assert part["withheld_links"] == 100
    with pytest.raises(KeyError):
        bundles.build(1, "client:00000000-0000-0000-0000-000000000000")


def test_a_key_gets_a_short_lived_link_to_its_clients_bundle(batch, clock):  # noqa: F811
    releases.create(batch["id"], "test reviewer")
    api = TestClient(app)
    without, _ = key_for("no-bundles")
    headers, created = key_for("with-bundles", bundle_downloads=True)
    refused = api.get("/v1/bundles/1", headers=without)
    assert (
        refused.status_code == 403 and refused.json()["title"] == "Bundles not in tier"
    )
    assert api.get("/v1/bundles/1", headers=headers).status_code == 404
    assert api.get("/v1/bundles/9", headers=headers).status_code == 404
    assert api.get("/v1/bundles/1").status_code == 401

    built = bundles.build(1, f"client:{created['client_id']}")
    bundles.build(1, f"client:{keys.create_client('other', 'no-bundles')['client_id']}")
    answer = api.get("/v1/bundles/1", headers=headers)
    assert answer.status_code == 200 and answer.headers["x-linklens-release"] == "1"
    body = answer.json()
    assert (body["sha256"], body["entities"], body["scope"]) == (
        built["artifact_sha"],
        50,
        f"client:{created['client_id']}",
    )
    assert body["manifest_sha256"] == built["manifest_sha"]
    assert body["size_bytes"] == built["size_bytes"]

    # The link needs no key and gives the archive itself.
    fetched = api.get(body["url"])
    assert fetched.status_code == 200
    assert fetched.headers["content-type"] == "application/gzip"
    assert hashlib.sha256(fetched.content).hexdigest() == built["artifact_sha"]

    token = body["url"].rsplit("/", 1)[1]
    expired, _ = download.sign(built["artifact_sha"], now=time.time() - 3600)
    other_artifact = store.blob(b"not a bundle", "text/plain", "note.txt")
    not_a_bundle, _ = download.sign(other_artifact)
    for bad in (expired, not_a_bundle, token[:-2] + "AA", "nonsense"):
        assert api.get(f"/v1/bundles/download/{bad}").status_code == 404

    # A tier narrowed after the bundle was built no longer gets those files.
    keys.set_tier(
        "with-bundles",
        rate_per_minute=600,
        interfaces=("rest", "mcp"),
        bundle_downloads=True,
        source_scope=["source-a"],
    )
    stale = api.get("/v1/bundles/1", headers=headers)
    assert stale.status_code == 409 and stale.json()["title"] == "Bundle out of date"
    narrowed = bundles.build(1, f"client:{created['client_id']}")
    fresh = api.get("/v1/bundles/1", headers=headers).json()
    assert fresh["sha256"] == narrowed["artifact_sha"] != built["artifact_sha"]

    with db.session() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM serving.bundle")).scalar()
            == 2
        )
    with pytest.raises(DBAPIError, match="permission denied"):
        with db.session() as connection:
            connection.execute(text("SELECT * FROM ops.release_bundle"))


def test_the_entity_viewer_draws_the_edges_of_the_full_viewer(
    batch,
    clock,  # noqa: F811
    monkeypatch,
):
    releases.create(batch["id"], "test reviewer")
    api = TestClient(app)
    headers, created = key_for("viewer", bundle_downloads=True)
    whole = bundles.build(1, f"client:{created['client_id']}")
    full_nodes, full_edges = graph(
        unpack(whole["artifact_sha"])["viewer.html"].decode()
    )

    queries._viewers.clear()
    built = []
    original = bundles.entity_viewer
    monkeypatch.setattr(
        bundles,
        "entity_viewer",
        lambda *a, **k: built.append(a[2]) or original(*a, **k),
    )
    for entity_id in entities_of(batch)[:5]:
        answer = api.get(f"/v1/entities/{entity_id}/viewer", headers=headers)
        assert answer.status_code == 200
        assert answer.headers["content-type"].startswith("text/html")
        version = store.get("profiles", f"{batch['id']}:{entity_id}")["profile_version"]
        assert answer.headers["etag"] == f'"{version}"'
        nodes, edges = graph(answer.text)
        me = render.entity_path(entity_id)[1:].removesuffix(".md")
        # One entity, its four cited observations and its two sources.
        assert me in nodes and len(nodes) == 7 and nodes <= full_nodes
        assert edges == {e for e in full_edges if e[0] in nodes and e[1] in nodes}
        assert len({e for e in edges if e[0] == me}) == 4

        again = api.get(
            f"/v1/entities/{entity_id}/viewer",
            headers={**headers, "If-None-Match": answer.headers["etag"]},
        )
        assert again.status_code == 304
        assert (
            api.get(f"/v1/entities/{entity_id}/viewer", headers=headers).text
            == answer.text
        )
    assert len(built) == 5  # kept by profile version, not built again

    scoped, _ = key_for("scoped-viewer", source_scope=["source-a"])
    nodes, edges = graph(
        api.get(f"/v1/entities/{entity_id}/viewer", headers=scoped).text
    )
    assert len(nodes) == 4 and "sources/source-b" not in nodes
    assert api.get("/v1/entities/nobody/viewer", headers=headers).status_code == 404
    assert api.get(f"/v1/entities/{entity_id}/viewer").status_code == 401
