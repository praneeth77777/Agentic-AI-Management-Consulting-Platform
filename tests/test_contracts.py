from app.models import Domain, Evidence, RoutingDecision


def test_routing_contract_normalizes_required_specialists() -> None:
    decision = RoutingDecision(
        intent="cross_domain_analysis",
        domains=[Domain.TECHNOLOGY, Domain.SEC, Domain.TECHNOLOGY],
        required_specialists=[Domain.CLINICAL],
        rationale="test",
        confidence=0.9,
    )

    assert decision.domains == [Domain.TECHNOLOGY, Domain.SEC]
    assert decision.required_specialists == [Domain.TECHNOLOGY, Domain.SEC]


def test_evidence_contract_preserves_required_ingestion_metadata() -> None:
    item = Evidence(
        evidence_id="tech-1",
        content="chunk",
        source_title="Cisco Guide",
        domain=Domain.TECHNOLOGY,
        organization="Cisco",
        publication_date="2026-01-01",
        document_type="manual",
        company_or_product="ISR4331",
        page_number=12,
        section="Diagnostics",
        source_path="data/raw/cisco.pdf",
        chunk_index=3,
        content_hash="abc123",
        ingested_at="2026-10-17T20:00:00Z",
        score=0.91,
    )

    assert item.company_or_product == "ISR4331"
    assert item.chunk_index == 3
    assert item.content_hash == "abc123"
    assert item.ingested_at.endswith("Z")
