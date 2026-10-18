from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class Domain(str, Enum):
    technology = "technology"
    clinical = "clinical"
    sec = "sec"
    csr = "csr"

class Evidence(BaseModel):
    evidence_id: str
    domain: Domain
    source_title: str
    organization: str | None = None
    document_type: str | None = None
    source_path: str
    page_number: int | None = None
    section: str | None = None
    content: str
    score: float = 0.0

class RoutingDecision(BaseModel):
    detected_intent: str
    domains: list[Domain]
    required_specialists: list[Domain]
    extracted_entities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    rationale: str
    needs_clarification: bool = False

class SpecialistReport(BaseModel):
    domain: Domain
    findings: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    candidate_recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    human_review_required: bool = False

class VerificationResult(BaseModel):
    passed: bool
    unsupported_evidence_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ConsultingRecommendation(BaseModel):
    executive_summary: str
    selected_domains: list[Domain]
    evidence: list[Evidence] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    human_review_required: bool = False

class QueryRequest(BaseModel):
    question: str = Field(min_length=3)

class QueryResponse(BaseModel):
    request_id: str
    route: RoutingDecision
    reports: list[SpecialistReport]
    verification: VerificationResult
    recommendation: ConsultingRecommendation
    latency_ms: float

class GraphState(BaseModel):
    request_id: str
    question: str
    route: RoutingDecision | None = None
    reports: list[SpecialistReport] = Field(default_factory=list)
    evidence: dict[str, list[Evidence]] = Field(default_factory=dict)
    verification: VerificationResult | None = None
    recommendation: ConsultingRecommendation | None = None
    errors: list[str] = Field(default_factory=list)
    retries: int = 0
    timings: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
