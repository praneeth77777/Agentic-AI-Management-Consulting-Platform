from __future__ import annotations
from app.agents.ollama_client import OllamaJSONClient
from app.models.contracts import ConsultingRecommendation, Domain, Evidence, SpecialistReport, VerificationResult

def synthesize(question: str, reports: list[SpecialistReport], evidence: list[Evidence], verification: VerificationResult, client: OllamaJSONClient | None = None) -> ConsultingRecommendation:
    if not reports:
        return ConsultingRecommendation(executive_summary="No specialist report was produced.", selected_domains=[], uncertainty=["No report available"], risks=["Insufficient evidence"], confidence=0.0)
    client = client or OllamaJSONClient()
    summary = "\n".join(f"{r.domain.value}: findings={r.findings}; recommendations={r.candidate_recommendations}; risks={r.risks}; evidence_ids={r.evidence_ids}" for r in reports)
    prompt = f"""You are the consulting manager. Synthesize specialist reports into a concise recommendation.
Question: {question}
Verification passed: {verification.passed}; warnings={verification.warnings}
Reports:\n{summary}
Return an executive summary, prioritized recommendations, uncertainty, risks, next actions, KPIs, confidence, human_review_required, and selected_domains. Do not add facts not present in specialist reports."""
    result = client.invoke_structured(prompt, ConsultingRecommendation)
    result.evidence = evidence
    if not verification.passed:
        result.confidence = min(result.confidence, 0.3)
        result.uncertainty.append("Evidence verification did not fully pass.")
    result.human_review_required = result.human_review_required or any(r.human_review_required for r in reports)
    return result
