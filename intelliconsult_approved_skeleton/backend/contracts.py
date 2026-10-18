from typing import Literal
from pydantic import BaseModel, Field
Domain = Literal['technology', 'clinical', 'sec', 'csr']
class ConsultRequest(BaseModel):
    question: str = Field(min_length=3)
class Evidence(BaseModel):
    id: str
    domain: Domain
    source: str
    page: int
    text: str
    retrieval: str = 'mock'
class Finding(BaseModel):
    domain: Domain
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
class Recommendation(BaseModel):
    domain: Domain
    action: str
    score: float | None = None
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
class ConsultReport(BaseModel):
    question: str
    selected_agents: list[Domain]
    needs_clarification: bool = False
    missing_information: list[str] = Field(default_factory=list)
    status: Literal['completed', 'needs_clarification'] = 'completed'
    findings: list[Finding]
    evidence: list[Evidence]
    recommendations: list[Recommendation]
    uncertainties: list[str]
    risks: list[str]
    next_actions: list[str]
    kpis: list[str]
    mode: str
