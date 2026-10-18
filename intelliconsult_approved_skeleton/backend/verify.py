
import re

from .contracts import Finding, Recommendation, Evidence


def _keywords(text: str) -> set[str]:
    """Extract meaningful words for a basic relevance check."""
    stop_words = {
        "the", "and", "for", "with", "that", "this",
        "from", "into", "when", "have", "has", "are",
        "our", "your", "router", "routers", "cisco",
        "series", "should", "before", "based"
    }

    words = re.findall(r"[a-z0-9]+", text.lower())

    return {
        word for word in words
        if len(word) > 2 and word not in stop_words
    }


def _is_relevant(claim: str, passage: str) -> bool:
    """
    Heuristic only: checks shared keywords.
    This does not establish factual entailment.
    """
    claim_words = _keywords(claim)
    passage_words = _keywords(passage)

    if not claim_words:
        return False

    overlap = len(claim_words & passage_words)

    return overlap >= 2


def _numbers_and_units(text: str) -> set[str]:
    """
    Extract numeric specifications such as 100 Gbps,
    60 Gbps, 2RU, 1RU, and 10GE.
    """
    import re

    pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:gbps|mbps|tbps|ge|ru)\b"
    )

    return {
        re.sub(r"\s+", "", match.lower())
        for match in re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )
    }


def _has_unsupported_specs(claim: str, passage: str) -> bool:
    claim_specs = _numbers_and_units(claim)
    passage_specs = _numbers_and_units(passage)

    return bool(claim_specs - passage_specs)



def verify(
    findings: list[Finding],
    recommendations: list[Recommendation],
    evidence: list[Evidence]
):
    evidence_by_id = {e.id: e for e in evidence}
    issues = []

    # Verify finding citations.
    for finding in findings:
        if not finding.evidence_ids:
            issues.append(
                f"Missing evidence for {finding.domain} finding"
            )
            continue

        valid_passages = []

        for evidence_id in finding.evidence_ids:
            source = evidence_by_id.get(evidence_id)

            if source is None:
                issues.append(
                    f"Invalid finding evidence ID: {evidence_id}"
                )
            elif source.domain != finding.domain:
                issues.append(
                    f"Cross-domain citation in {finding.domain} finding"
                )
            else:
                valid_passages.append(source)

        if valid_passages and not any(
            _is_relevant(finding.summary, e.text)
            for e in valid_passages
        ):
            issues.append(
                f"Low evidence relevance for {finding.domain} finding"
            )

    # Verify recommendation citations.
    for recommendation in recommendations:
        if not recommendation.evidence_ids:
            issues.append(
                f"No supporting citation for "
                f"{recommendation.domain} recommendation"
            )
            continue

        claim = (
            f"{recommendation.action} "
            f"{recommendation.rationale}"
        )

        for evidence_id in recommendation.evidence_ids:
            source = evidence_by_id.get(evidence_id)

            if source is None:
                issues.append(
                    f"Invalid recommendation evidence ID: {evidence_id}"
                )
                continue

            if source.domain != recommendation.domain:
                issues.append(
                    f"Cross-domain citation in "
                    f"{recommendation.domain} recommendation"
                )
                continue

            if not _is_relevant(claim, source.text):
                issues.append(
                    f"Low citation relevance for "
                    f"{recommendation.domain} recommendation "
                    f"(evidence {evidence_id})"
                )

            if _has_unsupported_specs(claim, source.text):
                issues.append(
                    f"Numeric specification not supported by "
                    f"cited passage in {recommendation.domain} "
                    f"recommendation (evidence {evidence_id})"
                )

    return issues