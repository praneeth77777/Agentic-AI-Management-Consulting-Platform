from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.ollama_client import OllamaJSONClient
from app.models.contracts import (
    ConsultingRecommendation,
    Domain,
    Evidence,
    SpecialistReport,
    VerificationResult,
)


class SynthesisDraft(BaseModel):
    """
    LLM-generated portion of the final recommendation.

    Evidence metadata is intentionally excluded. Evidence comes directly
    from retrieval and verification and must never be reconstructed by
    the language model.
    """

    executive_summary: str

    selected_domains: list[Domain] = Field(
        default_factory=list
    )

    recommendations: list[str] = Field(
        default_factory=list
    )

    uncertainty: list[str] = Field(
        default_factory=list
    )

    risks: list[str] = Field(
        default_factory=list
    )

    next_actions: list[str] = Field(
        default_factory=list
    )

    kpis: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    human_review_required: bool = False


def _verified_evidence(
    reports: list[SpecialistReport],
    evidence: list[Evidence],
) -> list[Evidence]:
    """
    Return only evidence actually cited by specialist reports.

    Evidence objects come from retrieval, so IDs, source titles, paths,
    page numbers, content, and scores remain deterministic.
    """

    cited_ids = {
        evidence_id
        for report in reports
        for evidence_id in report.evidence_ids
    }

    if not cited_ids:
        return []

    return [
        item
        for item in evidence
        if item.evidence_id in cited_ids
    ]


def synthesize(
    question: str,
    reports: list[SpecialistReport],
    evidence: list[Evidence],
    verification: VerificationResult,
    client: OllamaJSONClient | None = None,
) -> ConsultingRecommendation:
    if not reports:
        return ConsultingRecommendation(
            executive_summary=(
                "No specialist report was produced."
            ),
            selected_domains=[],
            evidence=[],
            uncertainty=[
                "No report available."
            ],
            risks=[
                "Insufficient evidence."
            ],
            confidence=0.0,
            human_review_required=False,
        )

    client = client or OllamaJSONClient()

    summary = "\n".join(
        (
            f"{report.domain.value}: "
            f"findings={report.findings}; "
            f"recommendations="
            f"{report.candidate_recommendations}; "
            f"risks={report.risks}; "
            f"assumptions={report.assumptions}; "
            f"missing_information="
            f"{report.missing_information}; "
            f"evidence_ids={report.evidence_ids}; "
            f"confidence={report.confidence}; "
            f"human_review_required="
            f"{report.human_review_required}"
        )
        for report in reports
    )

    expected_domains = [
        report.domain
        for report in reports
    ]

    prompt = f"""
You are the consulting manager.

Synthesize the specialist reports into one concise management
recommendation.

Question:
{question}

Verification:
passed={verification.passed}
warnings={verification.warnings}

Specialist reports:
{summary}

Requirements:
- Use only facts present in the specialist reports.
- Do not invent evidence IDs, citations, source titles, file paths,
  page numbers, or document metadata.
- Do not produce an evidence field.
- Do not introduce facts that are not supported by the reports.
- Preserve uncertainty when evidence is incomplete.
- For clinical matters, do not provide diagnosis or treatment advice.
- If any specialist requires human review, the final recommendation
  should also require human review.
- selected_domains must reflect only the specialist domains supplied
  above.

Return:
- executive_summary
- selected_domains
- recommendations
- uncertainty
- risks
- next_actions
- kpis
- confidence
- human_review_required
""".strip()

    draft = client.invoke_structured(
        prompt,
        SynthesisDraft,
    )

    # Do not allow the LLM to invent or omit routed domains.
    selected_domains = list(
        dict.fromkeys(expected_domains)
    )

    # Attach only real evidence referenced by specialist reports.
    final_evidence = _verified_evidence(
        reports,
        evidence,
    )

    confidence = draft.confidence

    uncertainty = list(
        draft.uncertainty
    )

    if not verification.passed:
        confidence = min(
            confidence,
            0.3,
        )

        uncertainty.append(
            "Evidence verification did not fully pass."
        )

    human_review_required = (
        draft.human_review_required
        or any(
            report.human_review_required
            for report in reports
        )
    )

    return ConsultingRecommendation(
        executive_summary=draft.executive_summary,
        selected_domains=selected_domains,
        evidence=final_evidence,
        recommendations=draft.recommendations,
        uncertainty=uncertainty,
        risks=draft.risks,
        next_actions=draft.next_actions,
        kpis=draft.kpis,
        confidence=confidence,
        human_review_required=human_review_required,
    )