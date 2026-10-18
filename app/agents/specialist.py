"""Evidence-grounded specialist shared by all four domain configurations."""
"""This file implements all four specialists using one shared class."""

from __future__ import annotations

import json
from statistics import fmean
from typing import Any

from app.models import ConfidenceComponents, Domain, Evidence, SpecialistReport
from app.retrieval import EvidenceRetriever


DOMAIN_INSTRUCTIONS: dict[Domain, str] = {
    Domain.TECHNOLOGY: (
        "Analyze technical symptoms, compatibility, remediation, procurement priority, "
        "and preventive maintenance. Never claim a component failed without diagnostics."
    ),
    Domain.CLINICAL: (
        "Analyze diagnostic or laboratory evidence. Do not diagnose or prescribe. "
        "State limitations and require qualified clinical or laboratory review."
    ),
    Domain.SEC: (
        "Analyze financial, competitive, operational, and filing risks. Distinguish "
        "company disclosures from your inferences and require financial review."
    ),
    Domain.CORPORATE_RESPONSIBILITY: (
        "Analyze food security, sustainability, ESG, and CSR outcomes. Connect actions "
        "to stakeholders and measurable impact indicators."
    ),
}


class SpecialistService:
    def __init__(self, model: Any, retriever: EvidenceRetriever, top_k: int = 5) -> None:
        self._model = model
        self._retriever = retriever
        self._top_k = top_k

    def analyze(
        self, question: str, domain: Domain
    ) -> tuple[SpecialistReport, list[Evidence]]:
        evidence = self._retriever.search(question, domain, limit=self._top_k)
        if not evidence:
            return self._empty_evidence_report(domain), []

        allowed_ids = [item.evidence_id for item in evidence]
        evidence_payload = [item.model_dump(mode="json") for item in evidence]
        system_prompt = f"""You are the {domain.value} specialist in a management consulting team.
{DOMAIN_INSTRUCTIONS[domain]}

Use only the supplied evidence. Cite claims with evidence_ids from this exact allowlist:
{allowed_ids}
Separate findings, assumptions, missing information, risks, recommendations, and suggested KPIs.
Every factual recommendation must include at least one supporting evidence_id.
If evidence is insufficient or conflicting, say so.
Do not invent a confidence score; the application calculates confidence from evidence quality and completeness.
Do not reveal chain-of-thought. Return only the requested structured result."""
        human_prompt = (
            f"Customer question:\n{question}\n\n"
            f"Retrieved evidence:\n{json.dumps(evidence_payload, indent=2)}"
        )

        try:
            structured = self._model.with_structured_output(
                SpecialistReport, method="json_schema"
            )
            result = structured.invoke(
                [("system", system_prompt), ("human", human_prompt)]
            )
            report = SpecialistReport.model_validate(result)
            return _attach_evidence_confidence(report, domain, evidence), evidence
        except Exception as exc:
            report = SpecialistReport(
                domain=domain,
                summary="The specialist could not produce a validated structured report.",
                missing_information=[
                    "Retry with a model that reliably supports Ollama structured output"
                ],
                risks=[f"Structured generation failure: {type(exc).__name__}"],
                confidence=0.0,
                requires_human_review=True,
            )
            return report, evidence

    @staticmethod
    def _empty_evidence_report(domain: Domain) -> SpecialistReport:
        limitation = (
            "Qualified clinical review is required."
            if domain == Domain.CLINICAL
            else "Human review is required before acting."
        )
        return SpecialistReport(
            domain=domain,
            summary=f"No indexed {domain.value} evidence was retrieved, so the agent abstained.",
            missing_information=[
                "Authoritative documents must be ingested and retrieved for this domain"
            ],
            recommendations=[],
            risks=[
                "Acting without source evidence could produce an unsupported decision",
                limitation,
            ],
            confidence_components=ConfidenceComponents(),
            confidence=0.0,
            requires_human_review=True,
        )


def _attach_evidence_confidence(
    report: SpecialistReport, domain: Domain, evidence: list[Evidence]
) -> SpecialistReport:
    retrieval_scores = {item.evidence_id: item.score for item in evidence}
    retrieval_relevance = fmean(retrieval_scores.values()) if retrieval_scores else 0.0

    source_quality_values: list[float] = []
    for item in evidence:
        # Source title and domain are validated contract fields. Additional metadata
        # raises the score without pretending metadata completeness proves truth.
        metadata = (
            item.organization,
            item.publication_date,
            item.document_type,
            item.page_number,
            item.section,
            item.source_path,
        )
        completeness = sum(value is not None for value in metadata) / len(metadata)
        source_quality_values.append(0.6 + 0.4 * completeness)
    source_quality = fmean(source_quality_values) if source_quality_values else 0.0

    missing_count = len(report.missing_information)
    information_completeness = max(0.0, 1.0 - 0.25 * missing_count)

    # Agreement requires semantic comparison that the starter does not yet perform.
    # Use a neutral value instead of a model self-rating until the verifier adds an
    # explicit contradiction check.
    components = ConfidenceComponents(
        retrieval_relevance=round(retrieval_relevance, 4),
        source_quality=round(source_quality, 4),
        evidence_agreement=0.5,
        information_completeness=round(information_completeness, 4),
    )
    return report.model_copy(
        update={
            "domain": domain,
            "retrieval_scores": retrieval_scores,
            "confidence_components": components,
            "confidence": components.overall(),
            "requires_human_review": True,
        }
    )
