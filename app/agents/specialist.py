from __future__ import annotations
from app.agents.ollama_client import OllamaJSONClient
from app.models.contracts import Domain, Evidence, SpecialistReport

DOMAIN_RULES = {
    Domain.technology: "Focus on diagnostics, product capability, compatibility limits, and technical next actions. Never invent part compatibility.",
    Domain.sec: "Focus on company filings, disclosed risks, financial/operational facts, and cited uncertainty. Require human review for financial interpretation.",
    Domain.clinical: "Decision support only. Do not diagnose or prescribe. Require human review.",
    Domain.csr: "Focus on food security, sustainability, CSR evidence, interventions, and measurable outcomes.",
}

def run_specialist(domain: Domain, question: str, evidence: list[Evidence], client: OllamaJSONClient | None = None) -> SpecialistReport:
    if not evidence:
        return SpecialistReport(domain=domain, missing_information=["No supporting evidence retrieved"], risks=["Insufficient evidence"], confidence=0.0, human_review_required=domain in {Domain.sec, Domain.clinical})
    client = client or OllamaJSONClient()
    packet = "\n\n".join(f"[{e.evidence_id}] {e.source_title} page={e.page_number}: {e.content[:1800]}" for e in evidence)
    prompt = f"""You are the {domain.value} specialist in a management consulting workflow.
Rules: {DOMAIN_RULES[domain]}
Question: {question}
Evidence:\n{packet}
Use only the evidence above for factual claims. Put only cited evidence IDs into evidence_ids. State assumptions, missing information, risks, candidate recommendations, and a confidence from 0 to 1 based on evidence quality/completeness."""
    report = client.invoke_structured(prompt, SpecialistReport)
    report.domain = domain
    allowed = {e.evidence_id for e in evidence}
    report.evidence_ids = [x for x in report.evidence_ids if x in allowed]
    if domain in {Domain.sec, Domain.clinical}:
        report.human_review_required = True
    return report
