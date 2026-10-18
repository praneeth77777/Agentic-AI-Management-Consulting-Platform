from app.agents.verifier import verify_reports
from app.models import CandidateRecommendation, Domain, Evidence, SpecialistReport


def evidence(evidence_id: str, domain: Domain) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        content="Test evidence",
        source_title="Test Source",
        domain=domain,
        score=0.9,
    )


def test_verifier_accepts_same_domain_supported_recommendation() -> None:
    report = SpecialistReport(
        domain=Domain.TECHNOLOGY,
        summary="Supported report",
        findings=["Supported finding"],
        evidence_ids=["tech-1"],
        recommendations=[
            CandidateRecommendation(
                action="Inspect logs",
                why="The evidence supports inspection.",
                evidence_ids=["tech-1"],
            )
        ],
    )

    result = verify_reports([report], [evidence("tech-1", Domain.TECHNOLOGY)])

    assert result.passed is True
    assert result.supported_evidence_ids == ["tech-1"]
    assert result.rejected_evidence_ids == []


def test_verifier_rejects_uncited_recommendation() -> None:
    report = SpecialistReport(
        domain=Domain.TECHNOLOGY,
        summary="Report",
        evidence_ids=["tech-1"],
        recommendations=[
            CandidateRecommendation(
                action="Replace the component",
                why="Unsupported in this test",
                evidence_ids=[],
            )
        ],
    )

    result = verify_reports([report], [evidence("tech-1", Domain.TECHNOLOGY)])

    assert result.passed is False
    assert result.unsupported_recommendations == ["Replace the component"]


def test_verifier_rejects_cross_domain_citation() -> None:
    report = SpecialistReport(
        domain=Domain.TECHNOLOGY,
        summary="Report",
        findings=["A technical finding"],
        evidence_ids=["sec-1"],
    )

    result = verify_reports(
        [report],
        [
            evidence("tech-1", Domain.TECHNOLOGY),
            evidence("sec-1", Domain.SEC),
        ],
    )

    assert result.passed is False
    assert result.rejected_evidence_ids == ["sec-1"]
    assert any("cross-domain" in warning for warning in result.warnings)


def test_verifier_rejects_unknown_evidence_id() -> None:
    report = SpecialistReport(
        domain=Domain.SEC,
        summary="Report",
        findings=["A filing finding"],
        evidence_ids=["invented-1"],
    )

    result = verify_reports([report], [evidence("sec-1", Domain.SEC)])

    assert result.passed is False
    assert result.rejected_evidence_ids == ["invented-1"]
