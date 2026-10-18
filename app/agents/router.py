"""Deterministic-first domain routing with an optional model fallback."""

from __future__ import annotations

import re
from typing import Any

from app.models import Domain, RoutingDecision


# Keep organization names out of domain terms. Cisco and Agilent appear in more
# than one project domain, so an entity name alone must not force a route.
DOMAIN_TERMS: dict[Domain, tuple[str, ...]] = {
    Domain.TECHNOLOGY: (
        "router",
        "network",
        "connectivity",
        "hardware",
        "software",
        "component",
        "replacement part",
        "technology investment",
        "cloud",
        "gcp",
    ),
    Domain.CLINICAL: (
        "clinical",
        "diagnostic",
        "laboratory",
        "patient",
        "medical",
        "assay",
        "sample",
        "instrument",
        "diabetes",
        "heart attack",
        "knee injury",
    ),
    Domain.SEC: (
        "sec filing",
        "10-k",
        "10-q",
        "annual report",
        "financial risk",
        "financial performance",
        "revenue",
        "cash flow",
        "shareholder",
        "securities",
        "competitive risk",
        "investor",
    ),
    Domain.CORPORATE_RESPONSIBILITY: (
        "food security",
        "sustainability",
        "sustainable",
        "esg",
        "csr",
        "hunger",
        "climate",
        "social responsibility",
    ),
}

KNOWN_ENTITIES = ("Cisco", "Agilent", "Alphabet", "Google", "IBM", "GCP")

ROUTER_SYSTEM_PROMPT = """You route enterprise consulting questions.
Choose only from: technology, clinical, sec, corporate_responsibility.
Select every genuinely needed domain. Do not answer the question.
Organization names such as Cisco or Agilent are entities, not domain signals by themselves.
Use SEC only for filings, financial performance, investor, or regulatory-risk analysis.
Set clarification_required=true only when critical information is required before safe retrieval or recommendation.
Return only the requested structured result."""


class RouterService:
    def __init__(self, model: Any | None, allow_model_fallback: bool = True) -> None:
        self._model = model
        self._allow_model_fallback = allow_model_fallback

    def route(self, question: str) -> RoutingDecision:
        deterministic = self._deterministic_route(question)
        if deterministic.domains or not self._allow_model_fallback or self._model is None:
            return deterministic
        try:
            structured = self._model.with_structured_output(
                RoutingDecision, method="json_schema"
            )
            result = structured.invoke(
                [("system", ROUTER_SYSTEM_PROMPT), ("human", question)]
            )
            return RoutingDecision.model_validate(result)
        except Exception as exc:  # Routing must fail closed rather than invent a route.
            return deterministic.model_copy(
                update={
                    "rationale": (
                        "No deterministic domain match; model routing failed: "
                        f"{type(exc).__name__}"
                    ),
                    "confidence": 0.0,
                    "clarification_required": True,
                }
            )

    @staticmethod
    def _deterministic_route(question: str) -> RoutingDecision:
        normalized = " ".join(question.lower().split())
        matched: list[Domain] = []
        for domain, terms in DOMAIN_TERMS.items():
            if any(term in normalized for term in terms):
                matched.append(domain)

        entities = [entity for entity in KNOWN_ENTITIES if entity.lower() in normalized]
        intent = _infer_intent(normalized, matched)
        missing, clarification_required = _missing_information(
            normalized, matched, entities, intent
        )

        if matched:
            rationale = "Matched explicit domain terminology: " + ", ".join(
                domain.value for domain in matched
            )
            confidence = min(0.98, 0.82 + 0.06 * len(matched))
        else:
            rationale = "No reliable domain terminology was found."
            confidence = 0.25
            missing = [
                "Which business domain is involved: technology, clinical, SEC, or corporate responsibility?",
                "What decision or outcome should the consulting team support?",
            ]
            clarification_required = True

        return RoutingDecision(
            intent=intent,
            domains=matched,
            required_specialists=matched,
            entities=entities,
            missing_information=missing,
            clarification_required=clarification_required,
            risk_level=_risk_level(matched),
            rationale=rationale,
            confidence=confidence,
        )


def _infer_intent(text: str, domains: list[Domain]) -> str:
    if len(domains) > 1:
        return "cross_domain_analysis"
    if any(term in text for term in ("failure", "replace", "troubleshoot", "repair")):
        return "technical_remediation"
    if Domain.SEC in domains:
        return "financial_and_operational_risk_analysis"
    if Domain.CLINICAL in domains:
        return "clinical_evidence_or_instrument_recommendation"
    if Domain.CORPORATE_RESPONSIBILITY in domains:
        return "sustainability_and_social_impact_strategy"
    if Domain.TECHNOLOGY in domains:
        return "technology_recommendation"
    return "needs_clarification"


def _missing_information(
    text: str,
    domains: list[Domain],
    entities: list[str],
    intent: str,
) -> tuple[list[str], bool]:
    missing: list[str] = []
    clarification_required = False

    if Domain.TECHNOLOGY in domains and intent == "technical_remediation":
        if not _has_product_model(text):
            missing.append("Exact product model and hardware revision")
            clarification_required = True
        if not any(
            term in text
            for term in (
                "log",
                "logs",
                "diagnostic",
                "diagnostics",
                "error",
                "errors",
                "alarm",
                "alarms",
                "interface reset",
                "packet loss",
            )
        ):
            missing.append("Relevant diagnostics, logs, and observed failure conditions")
            clarification_required = True

    if Domain.CLINICAL in domains and any(
        term in text for term in ("recommend", "select", "instrument", "assay")
    ):
        missing.append(
            "Laboratory requirements, sample type, throughput, and applicable approvals"
        )

    if Domain.SEC in domains and not entities:
        missing.append("Company name and filing period")
        clarification_required = True

    if Domain.CORPORATE_RESPONSIBILITY in domains and any(
        term in text for term in ("recommend", "strategy", "investment")
    ):
        missing.append("Target geography, population, budget, and desired outcome")

    return list(dict.fromkeys(missing)), clarification_required


def _has_product_model(text: str) -> bool:
    patterns = (
        r"\bisr[- ]?\d{3,5}\b",
        r"\basr[- ]?\d{3,5}\b",
        r"\bcatalyst[- ]?\d{3,5}\b",
        r"\bc\d{3,5}\b",
        r"\b[a-z]{2,6}-\d{3,6}[a-z0-9-]*\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _risk_level(domains: list[Domain]) -> str:
    if Domain.CLINICAL in domains or Domain.SEC in domains:
        return "high"
    if domains:
        return "medium"
    return "low"
