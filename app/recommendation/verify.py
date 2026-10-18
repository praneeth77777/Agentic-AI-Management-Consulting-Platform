from app.models.contracts import Evidence, SpecialistReport, VerificationResult

def verify_reports(reports: list[SpecialistReport], evidence_by_domain: dict[str, list[Evidence]]) -> VerificationResult:
    allowed = {e.evidence_id for items in evidence_by_domain.values() for e in items}
    used = {eid for r in reports for eid in r.evidence_ids}
    unsupported = sorted(used - allowed)
    warnings = []
    if any(not r.evidence_ids and r.findings for r in reports):
        warnings.append("A report contains findings without cited evidence IDs.")
    if any(r.confidence < 0.35 for r in reports):
        warnings.append("At least one specialist has low confidence.")
    return VerificationResult(passed=not unsupported and not any(not r.evidence_ids and r.findings for r in reports), unsupported_evidence_ids=unsupported, warnings=warnings)
