"""Immutable ontology contracts. Runtime activation never changes the submitted YAML."""

import hashlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class Concept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    definition: str = Field(min_length=12)
    type: Literal["string", "enum", "date", "boolean", "integer", "decimal"]
    scope: Literal[
        "entity",
        "address",
        "service_location",
        "contact",
        "licence",
        "registration",
        "financial_period",
    ]
    cardinality: Literal["one", "many"] = "one"
    values: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    minimum: str | None = None
    maximum: str | None = None

    @model_validator(mode="after")
    def coherent(self):
        namespace = self.name.split(".")[0]
        if namespace in {"observation", "confidence", "derivation_level"}:
            raise ValueError("Engine envelope namespaces are not mapping concepts")
        if namespace in {"entity", "address"} and self.scope != namespace:
            raise ValueError("Canonical namespace cannot change subject scope")
        if self.type == "enum" and (
            not self.values or len(set(self.values)) != len(self.values)
        ):
            raise ValueError("Enums require unique values")
        for bound in (self.minimum, self.maximum):
            if bound is not None and (
                self.type not in {"integer", "decimal"}
                or not Decimal(bound).is_finite()
            ):
                raise ValueError("Bounds require finite numeric types")
        if (
            self.minimum is not None
            and self.maximum is not None
            and Decimal(self.minimum) > Decimal(self.maximum)
        ):
            raise ValueError("Reversed numeric bounds")
        return self


@lru_cache
def legacy():
    raw = yaml.safe_load(
        Path(__file__).with_name("ontologies").joinpath("v0.1.yaml").read_text()
    )
    concepts = {}
    for scope in ("entity", "address"):
        for name, field in raw[scope].items():
            key = scope + "." + name
            concepts[key] = Concept(
                name=key,
                definition=field.get("notes") or "Canonical " + key + " source claim.",
                type=field["type"],
                scope=scope,
                cardinality="many" if key == "entity.trading_name" else "one",
                values=field.get("values", []),
            ).model_dump()
    return {"version": "0.1", "parent_hash": None, "concepts": concepts}


def resolve(ontology_hash=None):
    """The ontology document for a hash, rebuilt from the registry rows."""
    baseline = legacy()
    if ontology_hash is None or ontology_hash == digest(baseline):
        return baseline
    from . import store
    from .db import is_sha256
    from .db import ontology as registry

    document = None
    if is_sha256(ontology_hash):
        with store.engine().connect() as connection:
            document = registry.document(connection, ontology_hash)
    if document is None:
        raise KeyError(f"ontologies/{ontology_hash} not found")
    if digest(document) != ontology_hash:
        raise ValueError("Ontology content hash mismatch")
    return document


def validate_document(document, parent=None):
    concepts = document["concepts"]
    for name, raw in concepts.items():
        concept = Concept.model_validate(raw)
        if name != concept.name:
            raise ValueError("Concept key/name mismatch")
        if any(
            r not in concepts or concepts[r]["scope"] != concept.scope
            for r in concept.requires
        ):
            raise ValueError("Required companions must exist in the same scope")
    if parent:
        for name, concept in parent["concepts"].items():
            if concepts.get(name) != concept:
                raise ValueError("Experimental evolution must be additive")
        if document["parent_hash"] != digest(parent):
            raise ValueError("Wrong ontology parent")
    return document


def register(document, evidence=None):
    """Store a version, its concepts and its members in one transaction."""
    from . import store
    from .db import ontology as registry

    if not document.get("parent_hash") and document != legacy():
        raise ValueError("Only the packaged legacy ontology can be a root version")
    if document.get("parent_hash") == digest(legacy()):
        # The packaged root resolves without being stored; its children need its row.
        register(legacy())
    validate_document(
        document,
        resolve(document["parent_hash"]) if document.get("parent_hash") else None,
    )
    # Rows hold the canonical form of each concept. A document in another form
    # would be stored under a hash its rows no longer rebuild, so it is refused.
    if set(document) != {"version", "parent_hash", "concepts"} or any(
        raw != Concept.model_validate(raw).model_dump()
        for raw in document["concepts"].values()
    ):
        raise ValueError(
            "Ontology document is not in canonical form: every concept needs all "
            "fields, and only version, parent_hash and concepts are allowed at "
            "the top level"
        )
    key = digest(document)
    artifact = store.json_blob(document, "ontology.json")
    with store.engine().begin() as connection:
        if registry.insert_version(connection, key, document, artifact, digest):
            if digest(registry.document(connection, key)) != key:
                raise ValueError("Ontology rows do not rebuild the document's hash")
        if evidence:
            registry.add_evidence(connection, key, evidence)
    return key


def gate_for_promotion(connection, ontology_hash):
    """The gate run a promotion relies on. A missing or failed gate blocks it."""
    from .db import ontology as registry

    run = registry.latest_gate_run(connection, ontology_hash)
    if run is None:
        raise ValueError(
            "Promotion requires a gate report; run `link-lens ontology gate` first"
        )
    results = {check["check"]: check["result"] for check in run["checks"]}
    failed = sorted(name for name, result in results.items() if result == "fail")
    if failed:
        raise ValueError(
            "Promotion blocked by failed gate checks: " + ", ".join(failed)
        )
    return {"run_at": run["run_at"], "results": results}


def activate(ontology_hash, experiment_id, reviewer=None):
    """Append an activation. With a reviewer it is a promotion and needs a gate."""
    from . import store
    from .db import ontology as registry

    if ontology_hash == digest(legacy()):
        register(legacy())
    resolve(ontology_hash)
    record = {
        "ontology_hash": ontology_hash,
        "experiment_id": experiment_id,
        "reviewer": reviewer,
        "status": "promoted" if reviewer else "experimental",
        "created_at": store.now(),
    }
    with store.engine().begin() as connection:
        gate = gate_for_promotion(connection, ontology_hash) if reviewer else None
        registry.append_activation(connection, record, gate)
    # Unknown gate results travel with the promotion so the reviewer sees them.
    return {**record, "gate": gate} if gate else record


def active_hash(experiment_id):
    from . import store
    from .db import ontology as registry
    from .settings import settings

    with store.engine().connect() as connection:
        active = registry.latest_activation(connection, experiment_id)
    if active:
        return active["ontology_hash"]
    baseline = register(legacy())
    path = settings().ontology_path
    if path.exists():
        submitted = yaml.safe_load(path.read_text())
        if isinstance(submitted, dict) and "concepts" in submitted:
            return register(submitted)
    return baseline


# SKOS mapping relations a link to another vocabulary may have, and the LinkML
# slot each becomes in an export that includes the links.
MATCHES = {
    "exact": "exact_mappings",
    "close": "close_mappings",
    "broad": "broad_mappings",
    "narrow": "narrow_mappings",
    "related": "related_mappings",
}
IRI = re.compile(r'^https?://[^\s<>"]+$')


def _referenced_concept(connection, concept, ontology_hash):
    from .db import ontology as registry

    found = registry.concepts_named(connection, concept, ontology_hash)
    if not found:
        raise ValueError(
            f"No concept named {concept}"
            + (f" in ontology {ontology_hash}" if ontology_hash else "")
        )
    if len(found) > 1:
        raise ValueError(
            f"{concept} has {len(found)} definitions; name the ontology version "
            "whose definition the link is for"
        )
    return found[0]


def refer(concept, iri, match, reviewer, note=None, ontology_hash=None):
    """Record a person's link from a concept to a term of another vocabulary.

    The link is not part of any ontology version, so no hash or approval changes.
    Recording a link that already stands with the same match writes nothing.
    """
    from . import store
    from .db import ontology as registry

    if match not in MATCHES:
        raise ValueError("Match must be one of: " + ", ".join(MATCHES))
    if not IRI.fullmatch(iri):
        raise ValueError("The term must be an http or https IRI")
    if not reviewer:
        raise ValueError("A link is a person's decision; name the reviewer")
    with store.engine().begin() as connection:
        concept_id = _referenced_concept(connection, concept, ontology_hash)
        standing = {
            r["iri"]: r
            for r in registry.standing_references(connection)
            if r["concept_id"] == concept_id
        }
        if iri in standing and standing[iri]["match"] == match:
            return {**_reference(standing[iri]), "recorded": False}
        at = registry.append_reference(
            connection, concept_id, iri, match, "add", reviewer, note
        )
    return {
        "concept": concept,
        "iri": iri,
        "match": match,
        "reviewer": reviewer,
        "recorded_at": registry.iso(at),
        "recorded": True,
    }


def withdraw_reference(concept, iri, reviewer, note=None, ontology_hash=None):
    """Record that a person withdrew a link that stands."""
    from . import store
    from .db import ontology as registry

    if not reviewer:
        raise ValueError("Withdrawing a link is a person's decision; name the reviewer")
    with store.engine().begin() as connection:
        concept_id = _referenced_concept(connection, concept, ontology_hash)
        standing = next(
            (
                r
                for r in registry.standing_references(connection)
                if r["concept_id"] == concept_id and r["iri"] == iri
            ),
            None,
        )
        if standing is None:
            raise ValueError(f"No standing link from {concept} to {iri}")
        at = registry.append_reference(
            connection, concept_id, iri, standing["match"], "withdraw", reviewer, note
        )
    return {
        "concept": concept,
        "iri": iri,
        "match": standing["match"],
        "reviewer": reviewer,
        "recorded_at": registry.iso(at),
        "withdrawn": True,
    }


def _reference(row):
    return {
        key: row[key] for key in ("concept", "iri", "match", "reviewer", "recorded_at")
    }


def references(concept=None):
    """The links that stand now, by concept name and term."""
    from . import store
    from .db import ontology as registry

    with store.engine().connect() as connection:
        rows = registry.standing_references(connection)
    return [
        {**_reference(row), "note": row["note"]}
        for row in rows
        if concept is None or row["concept"] == concept
    ]


def references_for(ontology_hash):
    """Standing links of one version's concepts, as {concept name: [link, ...]}."""
    from . import store
    from .db import ontology as registry

    with store.engine().connect() as connection:
        members = set(registry.concept_ids(connection, ontology_hash).values())
        rows = registry.standing_references(connection)
    found = {}
    for row in rows:
        if row["concept_id"] in members:
            found.setdefault(row["concept"], []).append(
                {"iri": row["iri"], "match": row["match"]}
            )
    return found


def proposal(proposal_id):
    """A stored proposal as the workflow returned it, or None."""
    from . import store
    from .db import ontology as registry

    with store.engine().connect() as connection:
        return registry.get_proposal(connection, proposal_id)


def proposals():
    from . import store
    from .db import ontology as registry

    with store.engine().connect() as connection:
        return registry.list_proposals(connection)


# Local names whose values extraction checks as identifiers, in any namespace
# (`extraction.extract`). A concept that holds an identifier under another
# name, such as registration.business_name_abn, is checked only by the
# operations its mapping chooses.
IDENTIFIER_CHECKS = {
    "abn": "11 digits with a valid ABN checksum",
    "acn": "9 digits with a valid ACN checksum",
    "nzbn": "13 digits",
}

# What `scalar` and `extraction.extract` require of a value of each type.
TYPE_CHECKS = {
    "enum": "One of the allowed values",
    "date": "A calendar date written YYYY-MM-DD",
    "boolean": "true or false, mapped explicitly from the source",
    "integer": "A whole number written in plain digits",
    "decimal": "A number written in plain decimal digits, kept as exact text",
}


def checks(concept):
    """The rules a concept implies and the steps that apply each one.

    `applied_at` names the steps: `mapping` (a mapping that breaks the rule
    fails validation and cannot be approved), `extraction` (a value that breaks
    it is quarantined, not stored) and `profile` (how profiles treat the stored
    claims). An empty list means no code applies the rule. The LinkML, SHACL
    and JSON Schema exports carry fewer of these rules; docs/ENGINEERING.md
    lists which.
    """
    found = []

    def rule(text, *applied_at):
        found.append({"rule": text, "applied_at": list(applied_at)})

    scope, local = concept["scope"], concept["name"].split(".", 1)[1]
    if concept["type"] in TYPE_CHECKS:
        rule(TYPE_CHECKS[concept["type"]], "extraction")
    if local in IDENTIFIER_CHECKS:
        rule(IDENTIFIER_CHECKS[local], "extraction")
    low, high = concept.get("minimum"), concept.get("maximum")
    if low is not None and high is not None:
        rule(f"Between {low} and {high}", "extraction")
    elif low is not None:
        rule(f"At least {low}", "extraction")
    elif high is not None:
        rule(f"At most {high}", "extraction")
    if concept["requires"]:
        rule(
            "Stated together with "
            + ", ".join(concept["requires"])
            + " in the same source record and group",
            "mapping",
            "extraction",
        )
    if scope in {"entity", "address"}:
        rule("Stated outside any group", "mapping")
    else:
        rule(
            f"Stated inside a {scope} group, which holds the {scope} claims of one "
            "source record and is never merged with another group",
            "mapping",
            "profile",
        )
    if concept["name"].startswith("address."):
        rule("Kept with the other address fields of the same source record", "profile")
    if concept["cardinality"] == "many":
        rule(
            "May have several values; profiles keep them all and choose none", "profile"
        )
    else:
        rule(
            "Profiles choose one value, or none when equally authoritative claims "
            "disagree",
            "profile",
        )
    rule(
        "The meaning in the definition, which a person checks when approving a mapping"
    )
    return found


def scalar(value, concept):
    """Decimals remain exact JSON strings; never introduce binary float rounding."""
    kind = concept["type"]
    value = str(value).strip()
    if not value:
        return None
    if kind == "enum" and value not in concept["values"]:
        raise ValueError("Value outside ontology enum")
    if kind == "date":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Date must use YYYY-MM-DD")
        date.fromisoformat(value)
    if kind == "boolean":
        if value.lower() not in {"true", "false"}:
            raise ValueError("Boolean requires an explicit true/false mapping")
        return value.lower() == "true"
    if kind in {"integer", "decimal"}:
        if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
            raise ValueError(
                "Numeric value needs explicit plain decimal representation"
            )
        try:
            number = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Invalid decimal") from exc
        if kind == "integer" and number != number.to_integral_value():
            raise ValueError("Expected integer")
        if concept.get("minimum") is not None and number < Decimal(concept["minimum"]):
            raise ValueError("Below ontology minimum")
        if concept.get("maximum") is not None and number > Decimal(concept["maximum"]):
            raise ValueError("Above ontology maximum")
        return int(number) if kind == "integer" else format(number, "f")
    return value
