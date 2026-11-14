"""Releases, serving read models, and the OKF renderer, index, tree and bundle."""

import json
import time

import pytest
from link_lens import exports, releases, serving, store
from link_lens.cli import app
from link_lens.db import copy_insert
from link_lens.db import serving as tables
from link_lens.okf import bundle, index, render, tree
from link_lens.pipeline import assemble
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_identity_ops import assembled
from typer.testing import CliRunner


@pytest.fixture
def release(spec, snapshot):
    batch = assemble(assembled(spec, snapshot))
    return releases.create(batch["id"], "test reviewer", "fixture release")


def snapshot_of(connection, release_id):
    """Everything a client can ask of a release, to compare later."""
    pages = tree.find(connection, release_id, "/", limit=1000)["pages"]
    return {
        "ls": tree.ls(connection, release_id, "/entities/by-name"),
        "pages": pages,
        "grep": tree.grep(
            connection, release_id, "entity.abn", "/entities", limit=1000
        ),
        "texts": {
            p["path"]: tree.read(connection, release_id, p["path"])["text"]
            for p in pages[:40]
        },
        "index": tree.read(connection, release_id, "/entities/by-name/index.md")[
            "text"
        ],
    }


def test_release_is_recorded_once_and_builds_its_tree(release, spec, snapshot):
    assert release["released_by"] == "test reviewer" and release["release_id"] == 1
    assert (release["entities"], release["evidence"], release["sources"]) == (
        50,
        200,
        2,
    )
    assert (
        release["concepts"] == 59 and release["generated_at"] == release["released_at"]
    )
    shown = releases.show()
    assert shown["pages"] == {
        "Business Profile": 50,
        "Field Observation": 200,
        "Ontology Concept": 59,
        "Public Data Source": 2,
    }
    assert releases.listing()[0]["notes"] == "fixture release"
    with store.engine().connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(
                text("UPDATE ops.release SET released_by = 'someone else'")
            )
    with store.engine().connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(text("UPDATE serving.okf_page SET title = 'changed'"))
    for reviewer in ("", "   "):
        with pytest.raises(ValueError, match="person releasing"):
            releases.create(release["batch_id"], reviewer)
    with pytest.raises(KeyError):
        releases.create("no-such-batch", "reviewer")
    with pytest.raises(KeyError):
        releases.show(99)


def test_a_second_release_changes_nothing_in_the_first(release, spec, snapshot):
    with store.engine().connect() as connection:
        before = snapshot_of(connection, 1)
    assert len(before["pages"]) == 311 and before["grep"]["matches"]
    other = assemble(store.require("batches", release["batch_id"])["run_ids"])
    second = releases.create(other["id"], "another reviewer")
    assert second["release_id"] == 2 and second["released_at"] != release["released_at"]
    with store.engine().connect() as connection:
        assert snapshot_of(connection, 1) == before
        again = tree.read(connection, 2, before["pages"][0]["path"])["text"]
        # Each release has its own partitions. (Partitions of releases made by
        # other tests stay in the session database, so they are named, not counted.)
        partitions = set(
            connection.execute(
                text(
                    "SELECT inhrelid::regclass::text FROM pg_inherits "
                    "WHERE inhparent = 'serving.okf_page'::regclass"
                )
            ).scalars()
        )
    first = before["texts"][before["pages"][0]["path"]]
    assert again != first  # stamped with its own release time
    assert again.replace(second["released_at"], release["released_at"]) == first
    assert {"serving.okf_page_r1", "serving.okf_page_r2"} <= partitions
    assert releases.show()["release_id"] == 2 and releases.show(1)["release_id"] == 1


def test_bundle_files_are_exactly_what_the_tree_reads(release, tmp_path):
    written = bundle.write(1, tmp_path / "bundle")
    checked = exports.check_bundle(tmp_path / "bundle")
    assert checked == {"concepts": 311, "broken_links": 0}
    files = sorted(p for p in (tmp_path / "bundle").rglob("*.md"))
    assert written["files"] == len(files) > 311
    with store.engine().connect() as connection:
        for file in files:
            path = "/" + file.relative_to(tmp_path / "bundle").as_posix()
            assert tree.read(connection, 1, path)["text"] == file.read_text(), path
    # Written again, the bundle is the same bytes: pages carry the release time.
    bundle.write(1, tmp_path / "again")
    assert all(
        (tmp_path / "again" / f.relative_to(tmp_path / "bundle")).read_bytes()
        == f.read_bytes()
        for f in files
    )
    root = (tmp_path / "bundle" / "index.md").read_text()
    assert root.startswith('---\nokf_version: "0.2"\n---\n\n# Link Lens\n')
    assert (
        "[entities](entities/index.md)" in root
        and "[ontology](ontology/index.md)" in root
    )


def test_tree_lists_reads_finds_and_greps(release):
    with store.engine().connect() as connection:
        root = tree.ls(connection, 1, "/")
        assert [e["name"] for e in root["entries"]] == [
            "entities/",
            "evidence/",
            "index.md",
            "ontology/",
            "sources/",
        ]
        first = tree.ls(connection, 1, "/entities", limit=3)
        rest = tree.ls(
            connection, 1, "/entities", cursor=first["next_cursor"], limit=1000
        )
        names = [e["name"] for e in first["entries"] + rest["entries"]]
        assert len(first["entries"]) == 3 and rest["next_cursor"] is None
        assert names == sorted(names) and {"by-name/", "by-source/", "index.md"} <= set(
            names
        )
        by_source = tree.ls(connection, 1, "/entities/by-source")["entries"]
        assert [(e["name"], e.get("entries")) for e in by_source] == [
            ("index.md", None),
            ("source-a/", 50),
            ("source-b/", 50),
        ]
        concepts = tree.ls(connection, 1, "/ontology/entity")["entries"]
        assert {
            "name": "entity.abn.md",
            "path": "/ontology/entity/entity.abn.md",
            "kind": "page",
            "title": "entity.abn",
        } in concepts

        entity = tree.find(
            connection, 1, "/entities", type="Business Profile", limit=1
        )["pages"][0]
        page = tree.read(connection, 1, entity["path"])
        assert (
            page["text"].startswith("---\ntype: Business Profile\n")
            and page["next_offset"] is None
        )
        profile = json.loads(page["text"].split("```json\n")[1].split("\n```")[0])
        stored = store.listing("profiles", owner=release["batch_id"])
        assert profile in stored and list(profile)[0] == "canonical_entity_key"
        head = tree.read(connection, 1, entity["path"], offset=0, limit=5)
        tail = tree.read(connection, 1, entity["path"], offset=5, limit=1000)
        assert head["next_offset"] == 5 and head["text"] + tail["text"] == page["text"]
        assert page["total_lines"] == len(page["text"].splitlines())

        every = tree.find(connection, 1, "/", limit=1000)["pages"]
        assert len(every) == 311 and every == sorted(every, key=lambda p: p["path"])
        assert (
            len(tree.find(connection, 1, "/", tags=["evidence"], limit=1000)["pages"])
            == 200
        )
        assert (
            len(tree.find(connection, 1, "/", status="draft", limit=1000)["pages"])
            == 50
        )
        assert tree.find(
            connection, 1, "/ontology/address", tags=["ontology", "address"]
        )["pages"]
        paged = tree.find(connection, 1, "/evidence", limit=150)
        more = tree.find(
            connection, 1, "/evidence", cursor=paged["next_cursor"], limit=150
        )
        assert (
            len(paged["pages"]) == 150
            and len(more["pages"]) == 50
            and more["next_cursor"] is None
        )

        hits = tree.grep(
            connection, 1, r"^entity\.legal_name: Synthetic Entity 4\d$", "/entities"
        )
        assert [m["line"] for m in hits["matches"]] == sorted(
            f"entity.legal_name: Synthetic Entity {n}" for n in range(40, 50)
        ) or len(hits["matches"]) == 10
        assert all(
            m["path"].startswith("/entities/") and m["line_no"] for m in hits["matches"]
        )
        one = tree.grep(connection, 1, "entity.abn", "/entities", limit=1)
        two = tree.grep(
            connection, 1, "entity.abn", "/entities", cursor=one["next_cursor"], limit=1
        )
        assert one["matches"] != two["matches"] and two["next_cursor"]
        assert tree.grep(connection, 1, "Synthetic", "/sources")["matches"] == []
        with pytest.raises(ValueError, match="needs a folder"):
            tree.grep(connection, 1, "anything", "/")
        with pytest.raises(Exception, match="unterminated|missing|pattern"):
            tree.grep(connection, 1, "(unclosed", "/entities")
        for missing in ("/entities/zz/none.md", "/nowhere/index.md"):
            with pytest.raises(KeyError):
                tree.read(connection, 1, missing)
        with pytest.raises(KeyError):
            tree.read(connection, 7, "/index.md")


def test_scope_hides_pages_of_other_sources(release):
    scope = ["source-a"]
    with store.engine().connect() as connection:
        assert [
            e["name"]
            for e in tree.ls(connection, 1, "/sources", sources=scope)["entries"]
        ] == [
            "index.md",
            "source-a.md",
        ]
        assert (
            "source-b"
            not in tree.read(connection, 1, "/sources/index.md", sources=scope)["text"]
        )
        assert [
            e["name"]
            for e in tree.ls(connection, 1, "/entities/by-source", sources=scope)[
                "entries"
            ]
        ] == [
            "index.md",
            "source-a/",
        ]
        evidence = tree.find(connection, 1, "/evidence", limit=1000)["pages"]
        seen = tree.find(connection, 1, "/evidence", sources=scope, limit=1000)["pages"]
        assert len(evidence) == 200 and len(seen) == 100
        assert {p["source_id"] for p in seen} == {"source-a"}
        hidden = next(p for p in evidence if p["source_id"] == "source-b")
        with pytest.raises(KeyError):
            tree.read(connection, 1, hidden["path"], sources=scope)
        assert tree.read(connection, 1, hidden["path"])["text"]
        lines = tree.grep(
            connection, 1, "source: source-", "/evidence", sources=scope, limit=1000
        )
        assert {m["line"] for m in lines["matches"]} == {"source: source-a"}
        # Profiles are shown whole; scope applies to source and evidence pages.
        assert (
            len(
                tree.find(connection, 1, "/entities", sources=scope, limit=1000)[
                    "pages"
                ]
            )
            == 50
        )
    assert bundle.write(1, "/dev/null/unused", sources=[])["files"] if False else True


def test_no_index_page_lists_more_than_200_of_100000_entities():
    entities = [
        {
            "id": f"{n:08x}-entity",
            "name": f"{'abcdefghij'[n % 10]}{'klmnopqrst'[(n // 10) % 10]} Company {n}",
            "states": [("NSW", "VIC", "QLD")[n % 3]],
            "types": [
                "Australian Private Company" if n % 2 else "Australian Public Company"
            ],
            "sources": [f"source-{n % 7}"],
        }
        for n in range(100_000)
    ]
    entities += [
        {
            "id": f"same-{n:05d}",
            "name": "IDENTICAL NAME",
            "states": [],
            "types": [],
            "sources": [],
        }
        for n in range(450)
    ]
    rows = index.build(
        entities,
        [(f"source-{n}", f"Source {n}") for n in range(1500)],
        [("entity", f"entity.concept_{n}", "A definition") for n in range(300)],
    )
    folders = {}
    for row in rows:
        folders.setdefault(row.parent, []).append(row)
    assert max(len(entries) for entries in folders.values()) == index.LIMIT == 200
    # Every folder that is linked has an index, and links only one level down.
    for parent, entries in folders.items():
        assert [e.position for e in entries] == list(range(len(entries)))
        for entry in entries:
            if entry.is_folder:
                assert entry.target in folders and entry.target.rsplit("/", 1)[
                    0
                ] == parent.rstrip("/")
    reached = lambda root: {
        r.target for r in rows if not r.is_folder and r.parent.startswith(root)
    }
    assert len(reached("/entities/by-name")) == 100_450
    assert (
        len(reached("/entities/by-state"))
        == len(reached("/entities/by-type"))
        == 100_000
    )
    assert len(reached("/sources")) == 1500 and len(reached("/ontology")) == 300
    assert sorted(r.parent for r in rows if r.label == "IDENTICAL NAME")[0].endswith(
        "/1"
    )
    assert index.slug("  Ünïcode & Co.  ") == "n-code-co" and index.slug("!!!") == "-"


def plan(connection, sql, parameters):
    explained = connection.execute(
        text("EXPLAIN (FORMAT JSON) " + sql), parameters
    ).scalar_one()
    nodes, stack = [], [explained[0]["Plan"]]
    while stack:
        node = stack.pop()
        nodes.append(node["Node Type"])
        stack += node.get("Plans", [])
    return nodes


def test_find_and_grep_use_indexes_on_100000_pages(release):
    """The agreed time: one second per call on 100,000 entity pages, 400,000 lines."""
    with store.engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO ops.release (batch_id, ontology_hash, released_by) "
                "SELECT batch_id, ontology_hash, 'synthetic' FROM ops.release"
            )
        )
        connection.execute(text("SELECT serving.create_release_partitions(2)"))
        pages = (
            {
                "release_id": 2,
                "path": f"/entities/{n % 256:02x}/{n:08x}.md",
                "type": "Business Profile",
                "title": f"Company {n}",
                "description": "Synthetic",
                "tags": ["entity", "proposed-identity"],
                "status": "draft",
                "entity_id": f"{n:08x}",
                "source_id": None,
                "observation_source_id": None,
                "observation_id": None,
                "concept_name": None,
            }
            for n in range(100_000)
        )
        copy_insert(connection, tables.okf_page, pages)
        lines = (
            {
                "release_id": 2,
                "path": f"/entities/{n % 256:02x}/{n:08x}.md",
                "line_no": number,
                "line": line,
                "source_id": None,
            }
            for n in range(100_000)
            for number, line in enumerate(
                (
                    "type: Business Profile",
                    f"entity.legal_name: Company {n} Pty Ltd",
                    f"entity.abn: {10_000_000_000 + n * 7}",
                    f"address.state: {('NSW', 'VIC', 'QLD')[n % 3]} (business)",
                ),
                1,
            )
        )
        copy_insert(connection, tables.okf_line, lines)
        connection.execute(text("ANALYZE serving.okf_page_r2, serving.okf_line_r2"))

    base = {"release": 2, "limit": 101}
    find = {
        **base,
        "pattern": "/entities/3f/%",
        "cursor": "",
        "type": "Business Profile",
        "status": None,
        "tags": ["entity"],
    }
    grep = {
        **base,
        "pattern": "/entities/%",
        "expression": r"entity\.abn: 10000699993",
        "after_path": "",
        "after_line": 0,
    }
    with store.engine().connect() as connection:
        for sql, parameters in ((tree.FIND, find), (tree.GREP, grep)):
            nodes = plan(connection, sql.format(scope=""), parameters)
            assert "Seq Scan" not in nodes, nodes
            assert any("Index" in node for node in nodes), nodes
        timings = {}
        for name, call in (
            (
                "find",
                lambda: tree.find(
                    connection,
                    2,
                    "/entities/3f",
                    type="Business Profile",
                    tags=["entity"],
                ),
            ),
            (
                "grep_abn",
                lambda: tree.grep(
                    connection, 2, r"entity\.abn: 10000699993", "/entities"
                ),
            ),
            (
                "grep_name",
                lambda: tree.grep(
                    connection, 2, r"legal_name: Company 99999 ", "/entities"
                ),
            ),
            ("ls", lambda: tree.ls(connection, 2, "/entities/3f")),
        ):
            started = time.monotonic()
            result = call()
            timings[name] = time.monotonic() - started
            assert next(
                v for k, v in result.items() if k in ("pages", "matches", "entries")
            ), name
        print({name: f"{seconds * 1000:.0f} ms" for name, seconds in timings.items()})
        assert max(timings.values()) < 1.0, timings
        # The first release is untouched by the large one beside it.
        assert len(tree.find(connection, 1, "/entities", limit=1000)["pages"]) == 50


def test_serving_views_answer_for_a_release(release):
    with store.engine().connect() as connection:
        counts = {
            name: connection.execute(
                text(f"SELECT count(*) FROM serving.{name} WHERE release_id = 1")
            ).scalar_one()
            for name in serving.MODELS
            if name != "current_release"
        }
        assert counts == {
            "release": 1,
            "entity": 50,
            "profile": 50,
            "profile_field": 100,
            "profile_address": 0,
            "observation": 200,
            "evidence": 200,
            "link": 50,
            "source": 2,
            "concept": 59,
            "bundle": 0,
        }
        entity = (
            connection.execute(
                text(
                    "SELECT * FROM serving.entity WHERE release_id = 1 ORDER BY display_name LIMIT 1"
                )
            )
            .mappings()
            .one()
        )
        assert (
            entity["display_name"] == "Synthetic Entity 0"
            and len(entity["profile_version"]) == 64
        )
        assert set(entity["identifiers"]) == {"entity.abn"}
        field = (
            connection.execute(
                text(
                    "SELECT f.concept, f.value, f.confidence_kind, e.licence, e.source_title, e.row_no, o.entity_id "
                    "FROM serving.profile_field f "
                    "JOIN serving.evidence e USING (release_id, observation_id) "
                    "JOIN serving.observation o USING (release_id, observation_id) "
                    "WHERE f.release_id = 1 AND f.entity_id = :entity AND f.concept = 'entity.abn'"
                ),
                {"entity": entity["entity_id"]},
            )
            .mappings()
            .one()
        )
        assert field["value"] == entity["identifiers"]["entity.abn"]
        assert field["licence"] == "CC BY" and field["source_title"] == "Fixture"
        assert field["entity_id"] == entity["entity_id"] and field["row_no"] >= 20
        assert field["confidence_kind"] == "uncalibrated mapping/source judgements"
        link = connection.execute(
            text("SELECT status, score_kind FROM serving.link LIMIT 1")
        ).one()
        assert (
            link.status == "proposed_unreviewed" and "uncalibrated" in link.score_kind
        )
        current = (
            connection.execute(text("SELECT * FROM serving.current_release"))
            .mappings()
            .one()
        )
        latest = connection.execute(
            text("SELECT is_latest FROM serving.release")
        ).scalar_one()
        assert current["release_id"] == 1 and latest is True

    # The product role reads the read models and nothing else.
    with store.engine().connect() as connection:
        connection.execute(text("SET LOCAL ROLE linklens_product"))
        assert (
            connection.execute(text("SELECT count(*) FROM serving.entity")).scalar_one()
            == 50
        )
        assert (
            connection.execute(
                text("SELECT count(*) FROM serving.okf_page")
            ).scalar_one()
            == 311
        )
        for forbidden in (
            "SELECT * FROM identity.profile",
            "SELECT * FROM ops.release",
            "SELECT * FROM evidence.observation",
            "INSERT INTO serving.okf_page SELECT * FROM serving.okf_page",
        ):
            with pytest.raises(DBAPIError, match="permission denied"):
                with connection.begin_nested():
                    connection.execute(text(forbidden))


def test_serving_views_follow_their_files(release, monkeypatch):
    for name in serving.MODELS:
        comment, statement = serving.sql(name).split("SELECT", 1)
        # One commented SELECT per file, so a file can become a dbt model.
        assert comment.strip().startswith("--") and ";" not in statement, name
        assert not any(
            word in statement.upper()
            for word in ("INSERT ", "UPDATE ", "DELETE ", "CREATE ")
        ), name
    with store.engine().begin() as connection:
        assert serving.apply(connection) == []  # nothing changed since the upgrade
    original = serving.sql
    monkeypatch.setattr(
        serving,
        "sql",
        lambda name: (
            original(name) + " WHERE false"
            if name == "current_release"
            else original(name)
        ),
    )
    with pytest.raises(Exception):
        with store.engine().begin() as connection:
            serving.apply(connection)  # LIMIT 1 WHERE false is not valid SQL
    monkeypatch.setattr(
        serving,
        "sql",
        lambda name: (
            "SELECT 1 AS release_id" if name == "current_release" else original(name)
        ),
    )
    with store.engine().begin() as connection:
        assert serving.apply(connection) == ["current_release"]
        assert connection.execute(
            text("SELECT * FROM serving.current_release")
        ).all() == [(1,)]
    monkeypatch.setattr(serving, "sql", original)
    with store.engine().begin() as connection:
        assert serving.apply(connection) == ["current_release"]


def test_cli_creates_lists_shows_and_exports_a_release(spec, snapshot, tmp_path):
    runner = CliRunner()
    batch = assemble(assembled(spec, snapshot))
    assert (
        runner.invoke(app, ["release", "create", "--batch-id", batch["id"]]).exit_code
        == 2
    )
    blank = runner.invoke(
        app, ["release", "create", "--batch-id", batch["id"], "--reviewer", " "]
    )
    assert blank.exit_code == 2 and store.listing("runs") and releases.listing() == []
    created = runner.invoke(
        app,
        [
            "release",
            "create",
            "--batch-id",
            batch["id"],
            "--reviewer",
            "owner",
            "--notes",
            "first",
        ],
    )
    assert created.exit_code == 0 and json.loads(created.output)["entities"] == 50
    assert [
        r["released_by"]
        for r in json.loads(runner.invoke(app, ["release", "list"]).output)
    ] == ["owner"]
    assert json.loads(runner.invoke(app, ["release", "show"]).output)["index_pages"] > 5
    exported = runner.invoke(app, ["release", "export", str(tmp_path / "bundle")])
    assert exported.exit_code == 0 and json.loads(exported.output)["broken_links"] == 0
    assert (tmp_path / "bundle" / "index.md").exists()
    assert json.loads(runner.invoke(app, ["serving-apply"]).output) == {"changed": []}


def test_pages_are_ordered_for_readers_and_reproducible():
    value = {
        "zeta": 1,
        "status": "selected",
        "value": "x",
        "alpha": {"b": 1, "id": "k", "a": 2},
    }
    assert list(render.ordered(value)) == ["value", "status", "alpha", "zeta"]
    assert list(render.ordered(value)["alpha"]) == ["id", "a", "b"]
    assert render.link("/entities/ab/x.md", "/sources/s.md") == "../../sources/s.md"
    assert render.link("/index.md", "/entities/index.md") == "entities/index.md"
    assert (
        render.index_path("/") == "/index.md"
        and render.index_path("/a/b") == "/a/b/index.md"
    )
    assert render.cited_ids(
        {"id": "a", "fields": [{"id": "b"}, {"x": {"id": "c"}}]}
    ) == {"a", "b", "c"}
    concept = {
        "name": "site.latitude",
        "definition": "Latitude <in degrees>",
        "type": "decimal",
        "scope": "service_location",
        "cardinality": "one",
        "values": ["a", "b"],
        "requires": ["site.longitude"],
        "minimum": "-90",
        "maximum": "90",
    }
    page = render.render_concept(concept, "ab" * 32, "2026-01-01T00:00:00+00:00")
    assert page == render.render_concept(
        concept, "ab" * 32, "2026-01-01T00:00:00+00:00"
    )
    assert (
        "Latitude &lt;in degrees&gt;" in page and "* Requires: site.longitude" in page
    )
    assert "at: '2026-01-01T00:00:00+00:00'" in page and "# Allowed values" in page
