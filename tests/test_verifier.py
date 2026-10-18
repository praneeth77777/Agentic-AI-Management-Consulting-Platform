from app.models.contracts import Domain, Evidence, SpecialistReport
from app.recommendation.verify import verify_reports

def ev():
    return Evidence(evidence_id="e1", domain=Domain.sec, source_title="x", source_path="x.pdf", content="evidence")

def test_verifier_accepts_known_id():
    r=SpecialistReport(domain=Domain.sec, findings=["x"], evidence_ids=["e1"])
    v=verify_reports([r], {"sec":[ev()]})
    assert v.passed

def test_verifier_rejects_unknown_id():
    r=SpecialistReport(domain=Domain.sec, findings=["x"], evidence_ids=["bad"])
    v=verify_reports([r], {"sec":[ev()]})
    assert not v.passed
