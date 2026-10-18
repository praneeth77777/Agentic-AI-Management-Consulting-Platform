from __future__ import annotations

from app.agents.ollama_client import OllamaJSONClient
from app.models.contracts import Domain, Evidence, SpecialistReport


DOMAIN_RULES = {
    Domain.technology: (
        "Focus on diagnostics, product capability, compatibility limits, "
        "and technical next actions. Never invent part compatibility."
    ),
    Domain.sec: (
        "Focus on company filings, disclosed risks, financial/operational facts, "
        "and cited uncertainty. Require human review for financial interpretation."
    ),
    Domain.clinical: (
        "Decision support only. Do not diagnose or prescribe. "
        "Require human review."
    ),
    Domain.csr: (
        "Focus on food security, sustainability, CSR evidence, "
        "interventions, and measurable outcomes."
    ),
}


def run_specialist(
    domain: Domain,
    question: str,
    evidence: list[Evidence],
    client: OllamaJSONClient | None = None,
) -> SpecialistReport:
    if not evidence:
        return SpecialistReport(
            domain=domain,
            missing_information=["No supporting evidence retrieved"],
            risks=["Insufficient evidence"],
            confidence=0.0,
            human_review_required=domain in {Domain.sec, Domain.clinical},
        )

    client = client or OllamaJSONClient()

    packet = "\n\n".join(
        (
            f"[{e.evidence_id}] "
            f"{e.source_title} "
            f"page={e.page_number}: "
            f"{e.content[:1800]}"
        )
        for e in evidence
    )

    valid_ids = [e.evidence_id for e in evidence]

    prompt = f"""
You are the {domain.value} specialist in a management consulting workflow.

DOMAIN RULES:
{DOMAIN_RULES[domain]}

USER QUESTION:
{question}

VALID EVIDENCE IDS:
{valid_ids}

EVIDENCE:
{packet}

Return a structured SpecialistReport.

STRICT REQUIREMENTS:
1. Use only the evidence above for factual claims.
2. Every factual finding must be supported by at least one evidence item.
3. evidence_ids MUST contain one or more IDs from VALID EVIDENCE IDS
   whenever findings are returned.
4. Do not invent, modify, shorten, or fabricate evidence IDs.
5. If a factual finding cannot be supported by the supplied evidence,
   omit that finding.
6. If the evidence is insufficient, put the limitation in missing_information
   and reduce confidence.
7. State assumptions explicitly.
8. State relevant risks explicitly.
9. Add candidate recommendations only when supported by the evidence.
10. Confidence must be between 0 and 1 and should reflect evidence quality,
    consistency, relevance, and completeness.
11. For SEC and Clinical domains, human_review_required must be true.
12. Do not include hidden reasoning or chain-of-thought.

Important:
- evidence_ids must be copied exactly from VALID EVIDENCE IDS.
- Do not return findings with an empty evidence_ids list.
""".strip()

    report = client.invoke_structured(prompt, SpecialistReport)

    # The workflow controls the domain.
    report.domain = domain

    # Reject any hallucinated evidence IDs even if the model emits them.
    allowed = {e.evidence_id for e in evidence}
    report.evidence_ids = [
        evidence_id
        for evidence_id in report.evidence_ids
        if evidence_id in allowed
    ]

    # If the model returned factual findings without valid citations,
    # treat those findings as unsupported rather than allowing them downstream.
    if report.findings and not report.evidence_ids:
        report.findings = []
        report.candidate_recommendations = []
        report.missing_information.append(
            "The specialist did not provide valid evidence IDs for its factual findings."
        )
        report.risks.append(
            "Unsupported factual findings were removed because no valid evidence citation was provided."
        )
        report.confidence = min(report.confidence, 0.3)

    if domain in {Domain.sec, Domain.clinical}:
        report.human_review_required = True

    return report