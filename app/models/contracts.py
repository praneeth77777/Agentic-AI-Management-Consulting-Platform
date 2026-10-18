"""Validated contracts shared across graph nodes.
    This file defines the Pydantic data structures passed between components. 
    These contracts prevent agents from returning arbitrary, inconsistent dictionaries.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Defines the four accepted domains:
class Domain(str, Enum):
    TECHNOLOGY = "technology"
    CLINICAL = "clinical"
    SEC = "sec"
    CORPORATE_RESPONSIBILITY = "corporate_responsibility"


#calculates confidence
class ConfidenceComponents(BaseModel):
    """Evidence-derived confidence components.

    These values are calculated by application code. They are not intended to be
    free-form model self-ratings.
    """

    retrieval_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    source_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_agreement: float = Field(default=0.5, ge=0.0, le=1.0)
    information_completeness: float = Field(default=0.0, ge=0.0, le=1.0)

    def overall(self) -> float:
        value = (
            0.40 * self.retrieval_relevance
            + 0.20 * self.source_quality
            + 0.15 * self.evidence_agreement
            + 0.25 * self.information_completeness
        )
        return round(max(0.0, min(1.0, value)), 4)

# Represents one retrieved document chunk.
class Evidence(BaseModel):
    evidence_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    domain: Domain
    organization: str | None = None
    publication_date: str | None = None
    document_type: str | None = None
    company_or_product: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    section: str | None = None
    source_path: str | None = None
    chunk_index: int | None = Field(default=None, ge=0)
    content_hash: str | None = None
    ingested_at: str | None = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)

# Stores the manager’s classification:
class RoutingDecision(BaseModel):
    intent: str = Field(min_length=1)
    domains: list[Domain] = Field(default_factory=list)
    required_specialists: list[Domain] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clarification_required: bool = False
    risk_level: Literal["low", "medium", "high"] = "medium"
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize(self) -> "RoutingDecision":
        self.domains = list(dict.fromkeys(self.domains))
        # For this prototype every selected domain maps to exactly one specialist.
        # Keep one source of truth so model output cannot create contradictory lists.
        self.required_specialists = list(self.domains)
        self.entities = list(dict.fromkeys(self.entities))
        self.missing_information = list(dict.fromkeys(self.missing_information))
        if not self.domains:
            self.clarification_required = True
        return self


class CandidateRecommendation(BaseModel):
    action: str = Field(min_length=1)
    why: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    expected_impact: str = "Unknown until validated"
    implementation_effort: Literal["low", "medium", "high", "unknown"] = "unknown"


#The standard output required from every specialist:
class SpecialistReport(BaseModel):
    domain: Domain
    summary: str = Field(min_length=1)
    findings: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    retrieval_scores: dict[str, float] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommendations: list[CandidateRecommendation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_kpis: list[str] = Field(default_factory=list)
    confidence_components: ConfidenceComponents = Field(default_factory=ConfidenceComponents)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_human_review: bool = True


class VerificationResult(BaseModel):
    passed: bool
    supported_evidence_ids: list[str] = Field(default_factory=list)
    rejected_evidence_ids: list[str] = Field(default_factory=list)
    unsupported_recommendations: list[str] = Field(default_factory=list)
    domain_coverage: dict[str, bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    action: str = Field(min_length=1)
    why: str = Field(min_length=1)
    priority: Literal["now", "next", "later"]
    evidence_ids: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    evidence_id: str
    source_title: str
    page_number: int | None = None
    section: str | None = None


#Defines the user-facing final output:
class ConsultingResponse(BaseModel):
    request_id: str
    answer: str = Field(min_length=1)
    selected_domains: list[Domain] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    confidence_components: ConfidenceComponents = Field(default_factory=ConfidenceComponents)
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True
