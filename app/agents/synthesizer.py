"""Manager synthesis that exposes recommendations, uncertainty, and citations."""
"""This file, synthesizer, acts as the Management Consulting Manager after specialists finish."""

from __future__ import annotations

import json
from statistics import fmean
from typing import Any

from app.models import (
    Citation,
    ConfidenceComponents,
    ConsultingResponse,
    Domain,
    Evidence,
    Recommendation,
    RoutingDecision,
    SpecialistReport,
    VerificationResult,
)


class SynthesisService:
    def __init__(self, model: Any) -> None:
        self._model = model

    def synthesize(
        self,
        request_id: str,
        question: str,
        route: RoutingDecision,
        reports: list[SpecialistReport],
        evidence: list[Evidence],
        verification: VerificationResult,
    ) -> ConsultingResponse:
        if not evidence or not verification.passed:
            return _abstention_response(request_id, route, reports, verification)

        all_evidence_by_id = {item.evidence_id: item for item in evidence}
        verified_evidence_by_id = {
            evidence_id: all_evidence_by_id[evidence_id]
            for evidence_id in verification.supported_evidence_ids
            if evidence_id in all_evidence_by_id
        }
        verified_evidence = [
            item.model_dump(mode="json") for item in verified_evidence_by_id.values()
        ]
        payload = {
            "question": question,
            "routing": route.model_dump(mode="json"),
            "specialist_reports": [report.model_dump(mode="json") for report in reports],
            "verified_evidence": verified_evidence,
            "verification": verification.model_dump(mode="json"),
        }
        system_prompt = """You are the manager of an evidence-grounded consulting team.
Synthesize the specialist reports into a concise consulting response.
Use only verified evidence IDs in citations and recommendation evidence_ids.
Every factual recommendation must include supporting verified evidence IDs.
Distinguish facts from uncertainty. Explain what to do next, why, risks, and measurable KPIs.
Never authorize purchases, trades, diagnoses, treatments, or regulatory decisions.
Clinical and financial conclusions require qualified human review.
Do not invent a confidence score; the application calculates confidence from evidence components.
Do not reveal chain-of-thought. Return only the requested structured result."""

        try:
            structured = self._model.with_structured_output(
                ConsultingResponse, method="json_schema"
            )
            raw = structured.invoke(
                [
                    ("system", system_prompt),
                    ("human", json.dumps(payload, indent=2)),
                ]
            )
            response = ConsultingResponse.model_validate(raw)
            return _sanitize_response(
                response,
                request_id,
                route.domains,
                verified_evidence_by_id,
                reports,
            )
        except Exception:
            return _deterministic_response(
                request_id, route, reports, verified_evidence_by_id, verification
            )


def clarification_response(request_id: str, route: RoutingDecision) -> ConsultingResponse:
    questions = route.missing_information or [
        "Which domain and business decision should the consulting team address?"
    ]
    return ConsultingResponse(
        request_id=request_id,
        answer="I need more information before routing this request safely.",
        selected_domains=route.domains,
        clarification_questions=questions,
        uncertainty=[route.rationale],
        confidence_components=ConfidenceComponents(),
        confidence=0.0,
        requires_human_review=True,
    )


def _abstention_response(
    request_id: str,
    route: RoutingDecision,
    reports: list[SpecialistReport],
    verification: VerificationResult,
) -> ConsultingResponse:
    missing = route.missing_information + [
        item for report in reports for item in report.missing_information
    ]
    risks = [item for report in reports for item in report.risks]
    return ConsultingResponse(
        request_id=request_id,
        answer=(
            "The request was routed, but the platform cannot make a source-grounded "
            "recommendation because sufficient verified evidence was not available."
        ),
        selected_domains=route.domains,
        risks=list(dict.fromkeys(risks)),
        next_actions=[
            "Provide or ingest authoritative documents for the selected domain(s)",
            "Run retrieval again and inspect the returned evidence before acting",
        ],
        uncertainty=list(dict.fromkeys(verification.warnings)),
        clarification_questions=list(dict.fromkeys(missing)),
        confidence_components=ConfidenceComponents(),
        confidence=0.0,
        requires_human_review=True,
    )


def _deterministic_response(
    request_id: str,
    route: RoutingDecision,
    reports: list[SpecialistReport],
    evidence_by_id: dict[str, Evidence],
    verification: VerificationResult,
) -> ConsultingResponse:
    recommendations: list[Recommendation] = []
    for report in reports:
        for candidate in report.recommendations:
            valid_ids = [item for item in candidate.evidence_ids if item in evidence_by_id]
            if not valid_ids:
                continue
            recommendations.append(
                Recommendation(
                    action=candidate.action,
                    why=candidate.why,
                    priority="next",
                    evidence_ids=valid_ids,
                )
            )
    citations = [
        _citation(evidence_by_id[item])
        for item in verification.supported_evidence_ids
        if item in evidence_by_id
    ]
    components = _aggregate_confidence(reports)
    return ConsultingResponse(
        request_id=request_id,
        answer=" ".join(report.summary for report in reports),
        selected_domains=route.domains,
        recommendations=recommendations,
        risks=list(dict.fromkeys(item for report in reports for item in report.risks)),
        next_actions=list(
            dict.fromkeys(item.action for report in reports for item in report.recommendations)
        ),
        kpis=list(dict.fromkeys(item for report in reports for item in report.suggested_kpis)),
        citations=citations,
        uncertainty=list(
            dict.fromkeys(
                route.missing_information
                + verification.warnings
                + [item for report in reports for item in report.assumptions]
                + [item for report in reports for item in report.missing_information]
            )
        ),
        confidence_components=components,
        confidence=components.overall(),
        requires_human_review=True,
    )


def _sanitize_response(
    response: ConsultingResponse,
    request_id: str,
    domains: list[Domain],
    evidence_by_id: dict[str, Evidence],
    reports: list[SpecialistReport],
) -> ConsultingResponse:
    clean_recommendations: list[Recommendation] = []
    for item in response.recommendations:
        valid_ids = [
            evidence_id
            for evidence_id in item.evidence_ids
            if evidence_id in evidence_by_id
        ]
        if not valid_ids:
            continue
        clean_recommendations.append(item.model_copy(update={"evidence_ids": valid_ids}))

    cited_ids = {
        evidence_id
        for item in clean_recommendations
        for evidence_id in item.evidence_ids
    }
    cited_ids.update(
        citation.evidence_id
        for citation in response.citations
        if citation.evidence_id in evidence_by_id
    )
    citations = [_citation(evidence_by_id[item]) for item in sorted(cited_ids)]
    components = _aggregate_confidence(reports)

    report_kpis = list(
        dict.fromkeys(item for report in reports for item in report.suggested_kpis)
    )
    kpis = list(dict.fromkeys(response.kpis + report_kpis))

    return response.model_copy(
        update={
            "request_id": request_id,
            "selected_domains": domains,
            "recommendations": clean_recommendations,
            "kpis": kpis,
            "citations": citations,
            "confidence_components": components,
            "confidence": components.overall(),
            "requires_human_review": True,
        }
    )


def _aggregate_confidence(reports: list[SpecialistReport]) -> ConfidenceComponents:
    if not reports:
        return ConfidenceComponents()

    return ConfidenceComponents(
        retrieval_relevance=round(
            fmean(report.confidence_components.retrieval_relevance for report in reports),
            4,
        ),
        source_quality=round(
            fmean(report.confidence_components.source_quality for report in reports), 4
        ),
        evidence_agreement=round(
            fmean(report.confidence_components.evidence_agreement for report in reports),
            4,
        ),
        information_completeness=round(
            fmean(
                report.confidence_components.information_completeness
                for report in reports
            ),
            4,
        ),
    )


def _citation(evidence: Evidence) -> Citation:
    return Citation(
        evidence_id=evidence.evidence_id,
        source_title=evidence.source_title,
        page_number=evidence.page_number,
        section=evidence.section,
    )
