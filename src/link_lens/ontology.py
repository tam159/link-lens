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
    baseline = legacy()
    if ontology_hash is None or ontology_hash == digest(baseline):
        return baseline
    from . import store

    record = store.require("ontologies", ontology_hash)
    document = store.read_json(record["artifact_id"])
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
    from . import store

    if not document.get("parent_hash") and document != legacy():
        raise ValueError("Only the packaged legacy ontology can be a root version")
    validate_document(
        document,
        resolve(document["parent_hash"]) if document.get("parent_hash") else None,
    )
    key = digest(document)
    artifact = store.json_blob(document, "ontology.json")
    record = {
        "id": key,
        "artifact_id": artifact,
        "parent_hash": document.get("parent_hash"),
        "version": document["version"],
    }
    store.put("ontologies", key, record, kind="ontology", immutable=True)
    if evidence:
        store.put(
            "ontology_events",
            digest({"ontology": key, "evidence": evidence}),
            {"ontology_hash": key, "evidence": evidence},
            kind="proposal_evidence",
            immutable=True,
        )
    return key


def activate(ontology_hash, experiment_id, reviewer=None):
    from . import store

    resolve(ontology_hash)
    record = {
        "ontology_hash": ontology_hash,
        "experiment_id": experiment_id,
        "reviewer": reviewer,
        "status": "promoted" if reviewer else "experimental",
        "created_at": store.now(),
    }
    store.put(
        "ontology_events",
        digest(record),
        record,
        experiment_id,
        record["status"],
        immutable=True,
    )
    store.put(
        "ontology_events", "active-" + experiment_id, record, experiment_id, "active"
    )
    return record


def active_hash(experiment_id):
    from . import store
    from .settings import settings

    active = store.get("ontology_events", "active-" + experiment_id)
    if active:
        return active["ontology_hash"]
    baseline = register(legacy())
    path = settings().ontology_path
    if path.exists():
        submitted = yaml.safe_load(path.read_text())
        if isinstance(submitted, dict) and "concepts" in submitted:
            return register(submitted)
    return baseline


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
