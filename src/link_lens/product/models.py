"""Response models. Evidence is part of the answer, never an optional extra.

Status, provenance, alternatives, the kind of a score, the basis of a timestamp
and the licence are required fields: a response that lacks one is a bug, not a
tier. Concept names are checked against the ontology of the release that
answered, the same names its generated JSON Schema lists.
"""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, ValidationInfo


def known_concept(value: str, info: ValidationInfo):
    names = (info.context or {}).get("concepts")
    if names is not None and value not in names:
        raise ValueError(f"{value} is not a concept of this release's ontology")
    return value


Concept = Annotated[str, AfterValidator(known_concept)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecordRef(Model):
    source_id: str | None
    record_id: str | None


class ObservationRef(Model):
    source_id: str
    observation_id: str


class Entity(Model):
    entity_id: str
    display_name: str | None
    identifiers: dict[str, str]
    status: str
    profile_version: str
    okf_path: str


class EntityList(Model):
    entities: list[Entity]
    next_cursor: str | None


class ProfileField(Model):
    concept: Concept
    status: str
    value: Any
    values: list[Any] | None
    decision: str | None
    temporal_caveat: str | None
    confidence: dict[str, Any] | None
    confidence_kind: str
    observation: ObservationRef | None
    provenance: list[dict[str, Any]]
    alternatives: list[dict[str, Any]]


class Address(Model):
    role: str | None
    source_id: str | None
    record_id: str | None
    fields: dict[str, Any]


class Profile(Model):
    entity_id: str
    profile_version: str
    policy_version: str | None
    status: str
    uncertainties: list[Any]
    fields: list[ProfileField]
    addresses: list[Address]
    groups: list[Any]
    source_records: list[Any]
    reconciliation: dict[str, Any] | None
    okf_path: str


class Citation(Model):
    observation_id: str
    source_id: str
    observed_at: str | None
    observed_at_basis: str | None


class Option(Model):
    value: Any
    confidence: dict[str, Any] | None
    evidence: list[Citation]


class Claim(Model):
    concept: Concept
    status: str
    value: Any
    values: list[Option] | None
    values_total: int | None
    decision: str | None
    temporal_caveat: str | None
    confidence: dict[str, Any] | None
    confidence_kind: str
    evidence: list[Citation]
    alternatives: list[Option]
    alternatives_total: int


class ClaimSet(Model):
    """Claims that one source record makes together: an address or a group."""

    source_id: str | None
    record_id: str | None
    fields: list[Claim]


class AddressSummary(ClaimSet):
    role: str | None


class GroupSummary(ClaimSet):
    group_id: str | None
    scope: str | None
    decision: str | None


class CitedSource(Model):
    source_id: str
    title: str | None
    licence: str
    licence_url: str | None


class ProfileSummary(Model):
    entity_id: str
    profile_version: str
    status: str
    uncertainties: list[Any]
    fields: list[Claim]
    addresses: list[AddressSummary]
    groups: list[GroupSummary]
    sources: list[CitedSource]
    okf_path: str


class Observation(Model):
    observation_id: str
    source_id: str
    record_id: str
    entity_id: str | None
    concept: Concept
    value: str
    raw_value: Any
    source_fields: list[str]
    group_name: str | None
    field_confidence: float
    source_reliability: float
    confidence_kind: str
    observed_at: datetime
    timestamp_basis: Literal["snapshot", "record"]
    timezone_assumed: bool
    ingested_at: datetime
    derivation_level: str
    licence: str
    licence_url: str | None


class ObservationList(Model):
    observations: list[Observation]
    next_cursor: str | None


class Record(Model):
    record_id: str
    sheet: str | None
    row_no: int | None
    locator: dict[str, Any]


class Snapshot(Model):
    snapshot_id: str
    format: str | None
    observed_at: datetime | None
    observed_at_basis: str | None
    retrieved_at: datetime | None


class SourceRef(Model):
    source_id: str
    title: str | None
    publisher: str | None
    portal: str | None


class Evidence(Model):
    observation: Observation
    record: Record
    snapshot: Snapshot
    source: SourceRef
    licence: str
    licence_url: str | None


class Link(Model):
    link_id: str | None
    entity_id: str | None
    rule: str | None
    rule_version: str | None
    score: float | None
    score_kind: str
    threshold: float | None
    status: str
    human_review_status: str | None
    records: list[RecordRef]
    evidence: dict[str, Any] | None


class Source(Model):
    source_id: str
    title: str | None
    publisher: str | None
    portal: str | None
    licence: str
    licence_url: str | None
    snapshot_id: str | None
    retrieved_at: datetime | None
    okf_path: str


class ConceptDefinition(Model):
    name: Concept
    scope: str
    datatype: str
    cardinality: Literal["one", "many"]
    definition: str
    minimum: str | None
    maximum: str | None
    allowed_values: list[str]
    requires: list[str]
    okf_path: str


class Release(Model):
    release_id: int
    ontology_hash: str
    released_at: datetime
    notes: str | None
    is_current: bool


class Problem(Model):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None


def check(model, data, concepts=None):
    """Validate an answer against its model and the release's concept names."""
    return model.model_validate(data, context={"concepts": concepts})


def check_all(model, items, concepts=None):
    return [check(model, item, concepts) for item in items]
