from .contracts import Finding, Recommendation, Evidence

def verify(findings: list[Finding], recommendations: list[Recommendation], evidence: list[Evidence]):
    valid={e.id for e in evidence}
    issues=[]
    for f in findings:
        if not f.evidence_ids or any(id not in valid for id in f.evidence_ids):
            issues.append(f'Unsupported or missing evidence for {f.domain} finding')
    for r in recommendations:
        if any(id not in valid for id in r.evidence_ids):
            issues.append(f'Invalid evidence reference in {r.domain} recommendation')
    # This is a citation-ID integrity check, not semantic faithfulness verification.
    return issues
