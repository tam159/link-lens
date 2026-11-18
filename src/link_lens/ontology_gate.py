"""Promotion gate: recorded checks an ontology version passes before promotion.

A gate run writes one `ontology.gate_report` row per check. Promotion needs the
latest run to hold no `fail`. `unknown` means a check could not be decided; it
does not block, and it is recorded with the promotion for the reviewer to see.
The impact check is a report: it passes once it has counted what a version's
new concepts already touch. The near-duplicate check fails only on a repeated
definition; a likely duplicate is `unknown`, for the reviewer to compare.
"""

import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime

from sqlalchemy import text

from . import ontology, ontology_export, store
from .db import ontology as registry

SAMPLE_PER_CONCEPT = 25
LITERALS = {
    "date": "date",
    "integer": "integer",
    "decimal": "decimal",
    "boolean": "boolean",
}


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
    """A sample of stored observations validates against the generated shapes."""
    try:
        import linkml  # noqa: F401
        import pyshacl
        from rdflib import BNode, Graph, Literal, Namespace
        from rdflib.namespace import RDF, SH, XSD
    except ImportError:
        return "unknown", {
            "reason": "linkml and pyshacl are not installed; "
            "run `uv sync --group ontology`"
        }
    with store.engine().connect() as connection:
        members = registry.concept_ids(connection, key)
        samples = connection.execute(
            text(
                """
                SELECT name, value, id FROM (
                    SELECT c.name, o.value, sha256_hex(o.id) AS id,
                           row_number() OVER (PARTITION BY o.concept_id ORDER BY o.id) AS n
                    FROM evidence.observation o
                    JOIN ontology.concept c ON c.id = o.concept_id
                    WHERE o.concept_id = ANY(:concepts)
                ) ranked WHERE n <= :limit ORDER BY name, id
                """
            ),
            {"concepts": list(members.values()), "limit": SAMPLE_PER_CONCEPT},
        ).all()
    if not samples:
        return "unknown", {
            "reason": "No stored observation uses this version's concepts"
        }

    namespace = Namespace(ontology_export.BASE)
    data, claims = Graph(), {}
    for sample in samples:
        concept = document["concepts"][sample.name]
        node = BNode()
        claims[node] = sample
        datatype = LITERALS.get(concept["type"])
        data.add((node, RDF.type, namespace[ontology_export.camel(concept["scope"])]))
        data.add(
            (
                node,
                namespace[
                    ontology_export.attribute_name(sample.name, concept["scope"])
                ],
                Literal(sample.value, datatype=XSD[datatype])
                if datatype
                else Literal(sample.value),
            )
        )
    shapes = Graph().parse(data=ontology_export.shacl(document, key), format="turtle")
    conforms, report, _ = pyshacl.validate(data, shacl_graph=shapes)
    violations = [
        {
            "observation": claims[focus].id,
            "concept": claims[focus].name,
            "value": claims[focus].value[:200],
            "message": str(report.value(result, SH.resultMessage) or "")[:300],
        }
        for result, focus in report.subject_objects(SH.focusNode)
        if focus in claims
    ]
    return ("pass" if conforms else "fail"), {
        "sampled": len(samples),
        "concepts_sampled": len({s.name for s in samples}),
        "sample_per_concept": SAMPLE_PER_CONCEPT,
        "violations": sorted(
            violations, key=lambda v: (v["concept"], v["observation"])
        )[:50],
        "violation_count": len(violations),
    }


def check_impact(key, document):
    """Mapping configs and observations that use each concept this version adds."""
    with store.engine().connect() as connection:
        members = registry.concept_ids(connection, key)
        parent = (
            registry.concept_ids(connection, document["parent_hash"])
            if document["parent_hash"]
            else {}
        )
        changed = {
            concept_id: name
            for name, concept_id in members.items()
            if parent.get(name) != concept_id
        }
        counts = {
            name: {"mapping_configs": 0, "observations": 0} for name in changed.values()
        }
        for column, sql in (
            (
                "mapping_configs",
                "SELECT concept_id, count(DISTINCT config_hash) FROM onboarding.mapping_field "
                "WHERE concept_id = ANY(:concepts) GROUP BY 1",
            ),
            (
                "observations",
                "SELECT concept_id, count(*) FROM evidence.observation "
                "WHERE concept_id = ANY(:concepts) GROUP BY 1",
            ),
        ):
            for concept_id, total in connection.execute(
                text(sql), {"concepts": list(changed)}
            ):
                counts[changed[concept_id]][column] = total
    return "pass", {
        "changed_concepts": len(changed),
        # A config that maps several of these concepts is counted once per concept.
        "mapping_config_uses": sum(c["mapping_configs"] for c in counts.values()),
        "observations": sum(c["observations"] for c in counts.values()),
        "by_concept": dict(sorted(counts.items())),
    }


# Near-duplicate concepts. A lexical score with no model call: words of the
# concept's local name and of its definition, cut to their first six letters,
# weighted by how rare they are in this version. It is an uncalibrated rule
# score, not a probability, and it misses synonyms that share no words (suburb
# and locality score about 0.4). The bands follow the AWS Context Ontology
# Accelerator's grounding service: a strong match is shown only when it stands
# out from the runner-up, because a top score the next candidate almost equals
# says the words are shared, not that one concept is meant. Thresholds were set
# on 2026-11-18 against the promoted version and three made-up synonyms.
LIKELY = 0.75
POSSIBLE = 0.4
FLAT_SPREAD = 0.05
NEAREST = 3
STOP_WORDS = frozenset(
    "a an and any are as at be by each for from in is it its no not of on one "
    "or that the this to which with".split()
)


def words(text):
    return [
        word[:6]
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in STOP_WORDS and (len(word) > 1 or word.isdigit())
    ]


def similarity(first, second, weight):
    """Cosine similarity of two word lists, each word weighted by its rarity."""
    left, right = Counter(first), Counter(second)
    dot = sum(n * right[w] * weight[w] ** 2 for w, n in left.items())
    norm = math.sqrt(sum((n * weight[w]) ** 2 for w, n in left.items())) * math.sqrt(
        sum((n * weight[w]) ** 2 for w, n in right.items())
    )
    return dot / norm if norm else 0.0


def nearest_concepts(document, added):
    """For each added concept, its closest other concepts with a score and band.

    The score averages two parts: the definitions compared, and the best of the
    names compared, the name against the other's name and definition, and both
    together. Pairs of two parent concepts are not compared; they were accepted
    before.
    """
    concepts = document["concepts"]
    text = {
        name: (words(name.split(".", 1)[1].replace("_", " ")), words(c["definition"]))
        for name, c in concepts.items()
    }
    seen = Counter(w for pair in text.values() for w in set(pair[0] + pair[1]))
    total = len(concepts)
    weight = defaultdict(
        lambda: math.log(1 + total) + 1,
        {w: math.log((1 + total) / (1 + n)) + 1 for w, n in seen.items()},
    )
    found = {}
    for name in sorted(added):
        own_name, own_definition = text[name]
        scored = []
        for other, (other_name, other_definition) in text.items():
            if other == name:
                continue
            names = max(
                similarity(own_name, other_name, weight),
                similarity(own_name + own_definition, other_name, weight),
                similarity(
                    own_name + own_definition, other_name + other_definition, weight
                ),
            )
            score = (similarity(own_definition, other_definition, weight) + names) / 2
            scored.append((round(score, 3), other))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        top, runner_up = scored[0][0], scored[1][0] if len(scored) > 1 else 0.0
        same_scope = concepts[scored[0][1]]["scope"] == concepts[name]["scope"]
        if same_scope and " ".join(own_definition) == " ".join(text[scored[0][1]][1]):
            band = "same_definition"
        elif top >= LIKELY and same_scope and top - runner_up >= FLAT_SPREAD:
            band = "likely"
        elif top >= POSSIBLE:
            band = "possible"
        else:
            band = "distinct"
        found[name] = {
            "band": band,
            "nearest": [
                {
                    "concept": other,
                    "score": score,
                    "same_scope": concepts[other]["scope"] == concepts[name]["scope"],
                }
                for score, other in scored[:NEAREST]
            ],
        }
    return found


def check_near_duplicates(key, document):
    """No added concept repeats the meaning of another concept of the version.

    Fails only when an added concept's definition, read as words, equals that
    of a concept in the same scope. A likely duplicate makes the result
    `unknown`, which does not block: a reviewer compares the definitions.
    """
    if not document["parent_hash"]:
        return "pass", {"root": True, "added": 0}
    parent = ontology.resolve(document["parent_hash"])["concepts"]
    added = set(document["concepts"]) - set(parent)
    if not added:
        return "pass", {"added": 0}
    found = nearest_concepts(document, added)
    bands = Counter(entry["band"] for entry in found.values())
    result = (
        "fail" if bands["same_definition"] else "unknown" if bands["likely"] else "pass"
    )
    flagged = {
        name: entry
        for name, entry in found.items()
        if entry["band"] in {"same_definition", "likely", "possible"}
    }
    return result, {
        "added": len(added),
        "score_kind": "lexical, uncalibrated",
        "thresholds": {
            "likely": LIKELY,
            "possible": POSSIBLE,
            "flat_spread": FLAT_SPREAD,
        },
        "bands": dict(sorted(bands.items())),
        "concepts": dict(sorted(flagged.items())),
    }


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
    "near_duplicates": check_near_duplicates,
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
