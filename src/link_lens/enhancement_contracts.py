"""Versioned experimental resolution contracts; scores are not calibrated."""

from typing import Literal
from pydantic import Field, model_validator
from .contracts import StrictModel

VERSION = "hybrid-evidence-2"
EMBEDDING_VERSION = "hybrid-evidence-2"
Ref = tuple[str, str]


class EnhancementPolicy(StrictModel):
    version: str = VERSION
    retrieval: Literal["fuzzy", "hybrid"] = "hybrid"
    top_k: int = Field(default=20, ge=1, le=100)
    threshold: float = Field(default=0.98, ge=0, le=1)
    margin: float = Field(default=0.10, ge=0, le=1)
    embedding_model: str = "text-embedding-3-small"
    dimensions: int = Field(default=1536, ge=1, le=1536)
    decision_model: str = "typesafe/jev-1.13"
    explanation_model: str = "gpt-6-luna"
    reconcile: bool = True
    fuzzy_floor: float = Field(default=0.80, ge=0, le=1)
    embedding_floor: float = Field(default=0.80, ge=-1, le=1)


class CandidateComparison(StrictModel):
    id: str
    left: Ref
    right: Ref
    methods: list[str]
    scores: dict[str, float]
    evidence_hash: str
    features: dict


class IdentityJudgment(StrictModel):
    choice: Literal[
        "same_entity", "related_distinct", "different", "insufficient_evidence"
    ]
    probabilities: dict[str, float]
    names_compatible: float = Field(ge=0, le=1)
    corroborated: float = Field(ge=0, le=1)
    ownership_clear: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def distribution(self):
        if set(self.probabilities) != {
            "same_entity",
            "related_distinct",
            "different",
            "insufficient_evidence",
        }:
            raise ValueError("Incomplete identity distribution")
        if (
            any(not 0 <= v <= 1 for v in self.probabilities.values())
            or abs(sum(self.probabilities.values()) - 1) > 0.01
        ):
            raise ValueError("Invalid identity probabilities")
        if self.probabilities[self.choice] < max(self.probabilities.values()):
            raise ValueError("Choice disagrees with distribution")
        return self


class PairDecision(StrictModel):
    comparison: CandidateComparison
    status: Literal["eligible", "deferred", "blocked", "pending"]
    reason: str
    judgment: IdentityJudgment | None = None
    response_artifact: str | None = None


class ClusterDecision(StrictModel):
    records: list[Ref]
    status: Literal["admitted", "deferred"]
    reason: str
    entity_id: str | None = None
    pair_ids: list[str] = Field(default_factory=list)


class EquivalenceJudgment(StrictModel):
    equivalent: float = Field(ge=0, le=1)


class ConflictAnnotation(StrictModel):
    outcome: Literal["inference", "insufficient_evidence"]
    explanation: str = Field(max_length=2000)
    observation_ids: list[str] = Field(min_length=1)


class ReconciliationDecision(StrictModel):
    field: str
    observation_ids: list[str]
    status: Literal["equivalent", "distinct", "pending"]
    score: float | None = Field(default=None, ge=0, le=1)
    response_artifact: str | None = None
