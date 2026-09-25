"""Only this declarative language can reach the production extractor."""

import hashlib
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from .ontology import legacy, resolve

FIELDS = set(legacy()["concepts"])


def content_hash(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Condition(StrictModel):
    field: str
    op: Literal["in", "not_in", "nonempty", "length"]
    values: list[str] = Field(default_factory=list)
    length: int | None = None


class Operation(StrictModel):
    op: Literal[
        "trim",
        "uppercase",
        "lowercase",
        "digits",
        "abn",
        "acn",
        "nzbn",
        "date",
        "enum",
        "split",
        "join",
        "constant",
        "postcode",
        "website",
        "integer",
        "decimal",
        "boolean",
        "indicator_categories",
    ]
    argument: str | None = Field(
        default=None,
        description="For date: Python strptime format such as %d/%m/%Y or %Y-%m-%d (never DD/MM/YYYY). For split/join: literal delimiter. For constant: literal value.",
    )
    values: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_argument(self):
        if self.op == "date" and self.argument is not None and "%" not in self.argument:
            raise ValueError(
                "Date argument must use strptime directives, e.g. %d/%m/%Y, not DD/MM/YYYY"
            )
        return self


class FieldMapping(StrictModel):
    source_fields: list[str]
    canonical_field: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    group: str | None = Field(
        default=None,
        description="MUST be null for entity/address scope, including new entity/address fields. For contact/service_location/licence/registration/financial_period scope, supply a group name shared only by same-scope fields in this row.",
    )
    transformations: list[Operation] = Field(min_length=1)
    when: list[Condition] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(min_length=8)

    @model_validator(mode="after")
    def target(self):
        for op in self.transformations:
            if op.op == "indicator_categories" and set(op.values) != set(
                self.source_fields
            ):
                raise ValueError(
                    "Indicator categories must account for each named source column"
                )
        if not self.source_fields and self.transformations[0].op != "constant":
            raise ValueError("A field requires source_fields or an explicit constant")
        return self

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        value = handler(self)
        if self.group is None:
            value.pop("group", None)
        return value


class ReaderSpec(StrictModel):
    format: Literal["csv", "xlsx", "json"]
    encoding: Literal["utf-8-sig", "utf-8", "cp1252", "latin-1"] = "utf-8-sig"
    delimiter: Literal[",", "\t", ";", "|"] = ","
    sheet: str | None = None
    header_row: int = Field(default=1, ge=1, le=50)
    json_records_path: list[str] = Field(default_factory=list)


class UnmappedField(StrictModel):
    source_field: str
    reason: str


class MappingSpec(StrictModel):
    ontology_hash: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")
    reader: ReaderSpec
    record_grain: str = Field(min_length=10)
    subject_role: Literal[
        "legal_entity",
        "business_name_holder",
        "licence_holder",
        "service_provider",
        "supplier",
        "reporting_group",
        "unknown",
    ]
    source_kind: Literal[
        "company_register",
        "business_name_register",
        "licence_register",
        "charity_register",
        "tax_disclosure",
        "service_locations",
        "other",
    ]
    subject_label_field: str | None = None
    address_role: Literal["registered", "business", "service_location", "unknown"] = (
        "unknown"
    )
    filters: list[Condition] = Field(default_factory=list)
    fields: list[FieldMapping] = Field(min_length=1)
    unmapped_fields: list[UnmappedField] = Field(
        description="Each unused SOURCE COLUMN exactly once. Never include a column referenced by any fields[].source_fields. Do not list ontology targets or duplicate columns."
    )
    observed_at_field: str | None = None
    observed_at_format: str | None = None
    timestamp_policy: Literal[
        "record_statement_else_publication", "publication_proxy"
    ] = "publication_proxy"
    source_reliability: float = Field(ge=0, le=1)
    limitations: list[str]

    @model_validator(mode="after")
    def coherent(self):
        concepts = resolve(self.ontology_hash)["concepts"]
        for field in self.fields:
            if field.canonical_field not in concepts:
                raise ValueError("Unknown ontology field")
            concept = concepts[field.canonical_field]
            if concept["scope"] not in {"entity", "address"} and not field.group:
                raise ValueError(
                    f"{field.canonical_field} has scope {concept['scope']}; group must be a nonempty name"
                )
            if field.group and concept["scope"] in {"entity", "address"}:
                raise ValueError(
                    f"{field.canonical_field} has scope {concept['scope']}; group MUST be null"
                )
            companions = {
                f.canonical_field for f in self.fields if f.group == field.group
            }
            if not set(concept["requires"]).issubset(companions):
                raise ValueError("Missing required companion fields")
        scopes = {}
        for field in self.fields:
            if field.group:
                scope = concepts[field.canonical_field]["scope"]
                if field.group in scopes and scopes[field.group] != scope:
                    raise ValueError("A group cannot mix subject scopes")
                scopes[field.group] = scope
        targets = [(f.canonical_field, f.group) for f in self.fields]
        if len(targets) != len(set(targets)):
            raise ValueError("Duplicate canonical mapping")
        mapped = {s for f in self.fields for s in f.source_fields}
        unmapped = [f.source_field for f in self.unmapped_fields]
        if len(unmapped) != len(set(unmapped)) or mapped.intersection(unmapped):
            raise ValueError(
                "Mapped/unmapped fields must be disjoint; "
                f"overlapping columns: {sorted(mapped.intersection(unmapped))}; "
                f"duplicate unmapped columns: {sorted({x for x in unmapped if unmapped.count(x) > 1})}. "
                "Remove those entries from unmapped_fields; list each genuinely unused source column once."
            )
        if (
            self.timestamp_policy == "record_statement_else_publication"
            and not self.observed_at_field
        ):
            raise ValueError("Record timestamp policy requires its source field")
        return self

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        value = handler(self)
        if self.ontology_hash is None:
            value.pop("ontology_hash", None)
        return value


class SemanticReview(StrictModel):
    acceptable: bool
    blocking_issues: list[str]
    warnings: list[str]
    evidence_checked: list[str]


class ExplorationRequest(StrictModel):
    code: str = Field(min_length=1, max_length=30_000)
    purpose: str = Field(min_length=5)


class SourceRequest(StrictModel):
    dataset_id: str
    portal: str = "https://data.gov.au/data"
    resource_id: str | None = None


class ReviewLabel(StrictModel):
    item_id: str
    verdict: Literal["yes", "no", "unsure"]
    reviewer: str = Field(min_length=1)
    evidence: str = Field(min_length=8)
