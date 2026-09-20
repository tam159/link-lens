"""Only this declarative language can reach the production extractor."""

import hashlib
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

FIELDS = {
    "entity.legal_name",
    "entity.trading_name",
    "entity.abn",
    "entity.acn",
    "entity.nzbn",
    "entity.entity_type",
    "entity.status",
    "entity.website",
    "entity.industry_code",
    "entity.date_registered",
    "address.full",
    "address.locality",
    "address.state",
    "address.postcode",
    "address.country",
}


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
    canonical_field: Literal[
        "entity.legal_name",
        "entity.trading_name",
        "entity.abn",
        "entity.acn",
        "entity.nzbn",
        "entity.entity_type",
        "entity.status",
        "entity.website",
        "entity.industry_code",
        "entity.date_registered",
        "address.full",
        "address.locality",
        "address.state",
        "address.postcode",
        "address.country",
    ]
    transformations: list[Operation] = Field(min_length=1)
    when: list[Condition] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(min_length=8)

    @model_validator(mode="after")
    def target(self):
        if self.canonical_field not in FIELDS:
            raise ValueError("Unknown ontology field")
        if not self.source_fields and self.transformations[0].op != "constant":
            raise ValueError("A field requires source_fields or an explicit constant")
        return self


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
        targets = [f.canonical_field for f in self.fields]
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
