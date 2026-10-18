"""Deterministic evidence checks before manager synthesis."""

from __future__ import annotations

from collections import defaultdict

from app.models import Evidence, SpecialistReport, VerificationResult


def verify_reports(
    reports: list[SpecialistReport], evidence: list[Evidence]
) -> VerificationResult:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    domains_by_id: dict[str, set[str]] = defaultdict(set)
    for item in evidence:
        domains_by_id[item.evidence_id].add(item.domain.value)

    supported: set[str] = set()
    rejected: set[str] = set()
    unsupported_recommendations: list[str] = []
    domain_coverage: dict[str, bool] = {}
    warnings: list[str] = []

    conflicting_ids = sorted(
        evidence_id for evidence_id, domains in domains_by_id.items() if len(domains) > 1
    )
    if conflicting_ids:
        rejected.update(conflicting_ids)
        warnings.append(
            "Duplicate evidence IDs were associated with more than one domain: "
            + ", ".join(conflicting_ids)
        )

    for report in reports:
        report_domain = report.domain.value
        domain_evidence_ids = {
            item.evidence_id for item in evidence if item.domain == report.domain
        }
        report_citations: set[str] = set(report.evidence_ids)
        for recommendation in report.recommendations:
            report_citations.update(recommendation.evidence_ids)
            if not recommendation.evidence_ids:
                unsupported_recommendations.append(recommendation.action)
                warnings.append(
                    f"{report_domain} recommendation lacks an evidence reference: "
                    f"{recommendation.action}"
                )

        valid_for_domain: set[str] = set()
        for evidence_id in report_citations:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                rejected.add(evidence_id)
                warnings.append(
                    f"{report_domain} cited unknown evidence ID: {evidence_id}"
                )
                continue
            if item.domain != report.domain:
                rejected.add(evidence_id)
                warnings.append(
                    f"{report_domain} cited cross-domain evidence ID {evidence_id} "
                    f"from {item.domain.value}."
                )
                continue
            if evidence_id in conflicting_ids:
                rejected.add(evidence_id)
                continue
            valid_for_domain.add(evidence_id)

        if not domain_evidence_ids:
            warnings.append(f"No retrieved evidence belongs to the {report_domain} domain.")

        needs_support = bool(report.findings or report.recommendations)
        domain_has_support = bool(valid_for_domain) if needs_support else bool(domain_evidence_ids)
        domain_coverage[report_domain] = domain_has_support
        if needs_support and not valid_for_domain:
            warnings.append(
                f"{report_domain} report contains factual output without same-domain evidence support."
            )
        supported.update(valid_for_domain)

    if not evidence:
        warnings.append(
            "No evidence was retrieved; the system must abstain from factual recommendations."
        )
    if not reports:
        warnings.append("No specialist report was produced.")

    passed = bool(reports and evidence)
    passed = passed and not rejected and not unsupported_recommendations
    passed = passed and all(domain_coverage.get(report.domain.value, False) for report in reports)

    return VerificationResult(
        passed=passed,
        supported_evidence_ids=sorted(supported),
        rejected_evidence_ids=sorted(rejected),
        unsupported_recommendations=list(dict.fromkeys(unsupported_recommendations)),
        domain_coverage=domain_coverage,
        warnings=list(dict.fromkeys(warnings)),
    )
