"""A small OKF bundle kept in the repository, and what must stay true of it.

The files under `tests/fixtures/okf_bundle` are what the renderer writes for
the records below. A change to the renderer shows up here as a difference in a
page. When the change is meant, write the files again with

    UPDATE_FIXTURES=1 uv run pytest tests/test_fixture_bundle.py

and review the difference like any other. No database is used.
"""

import json
import os
from pathlib import Path

from link_lens import bundles, exports
from link_lens.okf import bundle as tree_files
from link_lens.okf import index, render

ROOT = Path(__file__).parent / "fixtures" / "okf_bundle"
STAMP = "2026-01-01T00:00:00+00:00"
SOURCE = {
    "id": "fixture-register",
    "portal": "https://data.example.org",
    "metadata": {
        "title": "Fixture Company Register",
        "organization": {"title": "Fixture Registrar"},
        "license_title": "CC BY 4.0",
    },
}
CONCEPTS = {
    "entity.legal_name": {
        "name": "entity.legal_name",
        "scope": "entity",
        "type": "string",
        "cardinality": "one",
        "definition": "The registered legal name of the entity.",
        "minimum": None,
        "maximum": None,
        "requires": [],
        "values": [],
    },
    "address.state": {
        "name": "address.state",
        "scope": "address",
        "type": "enum",
        "cardinality": "one",
        "definition": "The state or territory of an address.",
        "minimum": None,
        "maximum": None,
        "requires": [],
        "values": ["NSW", "VIC"],
    },
}
ONTOLOGY_HASH = "0" * 64


def observation(number, field, value, row):
    return {
        "id": f"{number:064x}",
        "source_id": SOURCE["id"],
        "source_record_id": f"{row:064x}",
        "field": field,
        "value": value,
        "raw_value": [value],
        "source_fields": [field.split(".")[1]],
        "observed_at": "2025-06-01T00:00:00+00:00",
        "observed_at_basis": "publication proxy",
        "confidence": {"field_confidence": 0.9, "source_reliability": 0.9},
        "confidence_kind": "uncalibrated mapping/source judgements",
        "raw_locator": {"row": row, "sheet": "csv", "snapshot_sha": "f" * 64},
        "licence": "CC BY 4.0",
    }


def claim(stated):
    cited = {
        key: stated[key]
        for key in (
            "id",
            "source_id",
            "source_record_id",
            "value",
            "observed_at",
            "observed_at_basis",
            "confidence",
            "raw_locator",
        )
    }
    return {
        "value": stated["value"],
        "status": "selected",
        "decision": "Only one source states this field.",
        "confidence": stated["confidence"],
        "provenance": [cited],
        "alternatives": [],
    }


def records():
    name = observation(1, "entity.legal_name", "Fixture Holdings Pty Ltd", 7)
    state = observation(2, "address.state", "NSW", 7)
    profile = {
        "canonical_entity_key": "11111111-2222-5333-8444-555555555555",
        "profile_version": "a" * 64,
        "status": "profile_from_proposed_links",
        "uncertainties": ["Confidence components are uncalibrated."],
        "fields": {"entity.legal_name": claim(name)},
        "addresses": [{"role": "business", "fields": {"address.state": claim(state)}}],
        "source_records": [[SOURCE["id"], name["source_record_id"]]],
    }
    return profile, [name, state]


def files():
    """The bundle as `path: text`, from pure render functions."""
    profile, observations = records()
    pages = {render.source_path(SOURCE["id"]): render.render_source(SOURCE, STAMP)}
    concepts = []
    for name, concept in CONCEPTS.items():
        path = render.concept_path(concept["scope"], name)
        pages[path] = render.render_concept(concept, ONTOLOGY_HASH, STAMP)
        concepts.append((concept["scope"], name, concept["definition"]))
    for stated in observations:
        pages[render.evidence_path(stated["id"])] = render.render_evidence(
            stated, STAMP
        )
    pages[render.entity_path(profile["canonical_entity_key"])] = render.render_entity(
        profile, [(o["id"], o["field"]) for o in observations], STAMP
    )
    sources = [(SOURCE["id"], SOURCE["metadata"]["title"])]
    pages.update(index.pages(index.build([index.summary(profile)], sources, concepts)))
    return pages


def test_the_renderer_still_writes_the_kept_bundle(tmp_path):
    pages = files()
    if os.environ.get("UPDATE_FIXTURES"):
        for old in ROOT.rglob("*.md"):
            old.unlink()
        tree_files.put(ROOT, pages)
    kept = {
        "/" + path.relative_to(ROOT).as_posix(): path.read_text()
        for path in ROOT.rglob("*.md")
    }
    assert sorted(kept) == sorted(pages)
    for path, body in pages.items():
        assert kept[path] == body, path


def test_the_kept_bundle_is_sound_and_draws_its_evidence():
    checked = exports.check_bundle(ROOT)
    assert checked == {"concepts": 6, "broken_links": 0}
    html = bundles.viewer(ROOT)
    line = next(x for x in html.splitlines() if x.startswith("window.BUNDLE ="))
    graph = json.loads(line.removeprefix("window.BUNDLE = ").rstrip(";"))
    edges = {(e["data"]["source"], e["data"]["target"]) for e in graph["edges"]}
    entity = "entities/11/11111111-2222-5333-8444-555555555555"
    evidence = [f"evidence/00/{number:064x}" for number in (1, 2)]
    assert {edge for edge in edges if edge[0] == entity} == {
        (entity, page) for page in evidence
    }
    assert all((page, "sources/fixture-register") in edges for page in evidence)
    # A bundle made twice from one folder is the same bytes.
    assert bundles.archive(ROOT, 0) == bundles.archive(ROOT, 0)
