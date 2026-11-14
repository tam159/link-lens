"""Promotion gate: recorded checks an ontology version passes before promotion.

A gate run writes one `ontology.gate_report` row per check. Promotion needs the
latest run to hold no `fail`. `unknown` means a check could not be decided; it
does not block, and it is recorded with the promotion for the reviewer to see.
"""

import json
from datetime import UTC, datetime

from . import ontology, ontology_export, store
from .db import ontology as registry

AWAITS_OBSERVATIONS = (
    "Needs typed observations and mappings, which arrive in phase 2 of the "
    "production plan"
)


def check_registry_digest(key, document):
    """The rows rebuild the hash, and equal the original JSON artifact."""
    with store.engine().connect() as connection:
        artifact = registry.version(connection, key)["document_artifact"]
    same = store.read_json(artifact) == document and ontology.digest(document) == key
    return ("pass" if same else "fail"), {"document_artifact": artifact}


def check_linkml(key, document):
    """LinkML export lints clean and generates SHACL and JSON Schema."""
    try:
        import linkml  # noqa: F401
    except ImportError:
        return "unknown", {
            "reason": "linkml is not installed; run `uv sync --group ontology`"
        }
    from importlib.metadata import version

    schema = ontology_export.linkml_yaml(document, key)
    detail = {
        "linkml_version": version("linkml"),
        "linkml_artifact": store.blob(
            schema.encode(), "application/yaml", "ontology.linkml.yaml"
        ),
    }
    try:
        problems = ontology_export.lint(schema)
        names = json.loads(ontology_export.json_schema(document, key))["$defs"][
            "ConceptName"
        ]["enum"]
        ontology_export.shacl(document, key)
    except Exception as error:
        return "fail", {**detail, "error": f"{type(error).__name__}: {error}"[:2000]}
    if set(names) != set(document["concepts"]):
        problems.append(
            {
                "level": "error",
                "rule": "concept_names",
                "message": "JSON Schema concept names differ from the registry",
            }
        )
    detail["problems"] = problems[:100]
    return ("fail" if problems else "pass"), detail


def check_additive(key, document):
    """Every concept of the parent is present and unchanged."""
    if not document["parent_hash"]:
        return "pass", {"root": True, "concepts": len(document["concepts"])}
    parent = ontology.resolve(document["parent_hash"])["concepts"]
    concepts = document["concepts"]
    changed = sorted(n for n in parent if n in concepts and concepts[n] != parent[n])
    removed = sorted(n for n in parent if n not in concepts)
    return ("fail" if changed or removed else "pass"), {
        "parent_hash": document["parent_hash"],
        "parent_concepts": len(parent),
        "added": sorted(n for n in concepts if n not in parent),
        "changed": changed,
        "removed": removed,
    }


def check_shacl_observations(key, document):
    return "unknown", {"reason": AWAITS_OBSERVATIONS}


def check_impact(key, document):
    return "unknown", {"reason": AWAITS_OBSERVATIONS}


def check_open_ontologies(key, document):
    return "unknown", {
        "reason": "Optional check; no pinned Open Ontologies version is configured"
    }


CHECKS = {
    "registry_digest": check_registry_digest,
    "linkml": check_linkml,
    "additive": check_additive,
    "shacl_observations": check_shacl_observations,
    "impact": check_impact,
    "open_ontologies": check_open_ontologies,
}


def run(ontology_hash):
    """Run every check for a stored version and record one row per check."""
    if ontology_hash == ontology.digest(ontology.legacy()):
        ontology.register(ontology.legacy())
    document = ontology.resolve(ontology_hash)
    checks = []
    for name, check in CHECKS.items():
        try:
            result, detail = check(ontology_hash, document)
        except Exception as error:  # A check that cannot run has not passed.
            result = "fail"
            detail = {"error": f"{type(error).__name__}: {error}"[:2000]}
        checks.append({"check": name, "result": result, "detail": detail})
    run_at = datetime.now(UTC)
    with store.engine().begin() as connection:
        registry.insert_gate_run(connection, ontology_hash, checks, run_at)
    return {
        "ontology_hash": ontology_hash,
        "run_at": run_at.isoformat(),
        "checks": checks,
        "blocks_promotion": any(c["result"] == "fail" for c in checks),
    }
