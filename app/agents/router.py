import re

from app.models.contracts import Domain, RoutingDecision


TECH = {
    "router",
    "network",
    "switch",
    "catalyst",
    "asr",
    "isr",
    "sd-wan",
    "vpn",
    "gcp",
    "cloud",
    "infrastructure",
    "hardware",
    "software",
    "configuration",
    "troubleshoot",
    "troubleshooting",
    "upgrade",
    "modernization",
}


SEC = {
    "sec",
    "10-k",
    "10k",
    "10-q",
    "10q",
    "filing",
    "filings",
    "risk factor",
    "risk factors",
    "revenue",
    "financial condition",
    "financial results",
    "earnings",
    "annual report",
    "operational risk",
    "operational risks",
}


CLINICAL = {
    "clinical",
    "patient",
    "patients",
    "diabetes",
    "covid",
    "heart",
    "knee",
    "trial",
    "trials",
    "diagnosis",
    "treatment",
}


CSR = {
    "corporate responsibility",
    "food security",
    "food-security",
    "hunger",
    "nutrition",
    "fao",
    "sustainability",
    "csr",
    "sdg 2",
}


def _contains_term(
    text: str,
    term: str,
) -> bool:
    """
    Match complete words or phrases rather than arbitrary substrings.

    Example:
        "sec" matches "SEC filing"
        "sec" does NOT match "security"
    """

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(term.lower())
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        text.lower(),
    ) is not None


def _hits(
    text: str,
    words: set[str],
) -> int:
    return sum(
        1
        for word in words
        if _contains_term(
            text,
            word,
        )
    )


def _extract_entities(
    text: str,
) -> list[str]:
    entities = []

    if _contains_term(
        text,
        "cisco",
    ):
        entities.append(
            "Cisco"
        )

    if (
        _contains_term(
            text,
            "alphabet",
        )
        or _contains_term(
            text,
            "google",
        )
    ):
        entities.append(
            "Alphabet"
        )

    if _contains_term(
        text,
        "agilent",
    ):
        entities.append(
            "Agilent"
        )

    return entities


def route_question(
    question: str,
) -> RoutingDecision:
    text = question.lower()

    scores = {
        Domain.technology: _hits(
            text,
            TECH,
        ),
        Domain.sec: _hits(
            text,
            SEC,
        ),
        Domain.clinical: _hits(
            text,
            CLINICAL,
        ),
        Domain.csr: _hits(
            text,
            CSR,
        ),
    }

    domains: list[Domain] = []

    # Explicit SEC / filing language routes to SEC.
    if scores[Domain.sec] > 0:
        domains.append(
            Domain.sec
        )

    # Technology is selected only when technical intent is present.
    if scores[Domain.technology] > 0:
        domains.append(
            Domain.technology
        )

    if scores[Domain.clinical] > 0:
        domains.append(
            Domain.clinical
        )

    if scores[Domain.csr] > 0:
        domains.append(
            Domain.csr
        )

    # Company names are entities, not domain signals by themselves.
    #
    # Cisco-only questions default to Technology.
    # Alphabet/Agilent-only questions default to SEC.
    if not domains:
        if _contains_term(
            text,
            "cisco",
        ):
            domains = [
                Domain.technology
            ]

        elif (
            _contains_term(
                text,
                "alphabet",
            )
            or _contains_term(
                text,
                "agilent",
            )
        ):
            domains = [
                Domain.sec
            ]

        else:
            domains = [
                Domain.technology
            ]

    missing_information: list[str] = []
    needs_clarification = False

    if (
        Domain.technology in domains
        and any(
            _contains_term(
                text,
                phrase,
            )
            for phrase in [
                "replace",
                "compatible",
                "failure",
                "broken",
                "part",
            ]
        )
    ):
        model_match = re.search(
            (
                r"\b(?:"
                r"c8\d{3}|"
                r"asr\s*\d{4}|"
                r"isr\s*\d{4}|"
                r"catalyst\s*\d{4}"
                r")\b"
            ),
            text,
            re.I,
        )

        if not model_match:
            missing_information.append(
                "Exact product/model identifier"
            )

            needs_clarification = True

    if Domain.clinical in domains:
        risk_level = "high"

    elif Domain.sec in domains:
        risk_level = "medium"

    else:
        risk_level = "low"

    return RoutingDecision(
        detected_intent=(
            "enterprise consulting question"
        ),
        domains=domains,
        required_specialists=domains,
        extracted_entities=_extract_entities(
            text
        ),
        missing_information=missing_information,
        risk_level=risk_level,
        rationale=(
            "Deterministic intent routing using "
            "whole-word and phrase matching; "
            "company names are treated as entities "
            "rather than domain signals."
        ),
        needs_clarification=needs_clarification,
    )