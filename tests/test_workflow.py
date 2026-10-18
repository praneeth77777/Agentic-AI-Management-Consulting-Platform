from __future__ import annotations

from typing import Any

from app.graph import build_consulting_graph
from app.models import (
    CandidateRecommendation,
    ConsultingResponse,
    Domain,
    Evidence,
    Recommendation,
    SpecialistReport,
)
from app.retrieval import InMemoryRetriever, NullRetriever


class _StructuredFake:
    def __init__(self, schema: type[Any]) -> None:
        self.schema = schema

    def invoke(self, messages: list[tuple[str, str]]) -> Any:
        if self.schema is SpecialistReport:
            is_sec = "sec specialist" in messages[0][1].lower()
            domain = Domain.SEC if is_sec else Domain.TECHNOLOGY
            evidence_id = "sec-1" if is_sec else "tech-1"
            return SpecialistReport(
                domain=domain,
                summary="The evidence supports collecting diagnostics before replacement.",
                findings=["The retrieved test evidence requires diagnostic confirmation."],
                evidence_ids=[evidence_id],
                recommendations=[
                    CandidateRecommendation(
                        action="Collect device diagnostics",
                        why="Confirm the failure mode before ordering parts.",
                        evidence_ids=[evidence_id],
                        implementation_effort="low",
                    )
                ],
                suggested_kpis=["Repeat outage rate"],
            )
        if self.schema is ConsultingResponse:
            return ConsultingResponse(
                request_id="model-must-not-control-this",
                answer="Collect diagnostics before selecting replacement parts.",
                selected_domains=[Domain.TECHNOLOGY],
                recommendations=[
                    Recommendation(
                        action="Collect device diagnostics",
                        why="Validate the failure mode.",
                        priority="now",
                        evidence_ids=["tech-1"],
                    )
                ],
                next_actions=["Capture logs"],
                kpis=["Repeat outage rate"],
                confidence=0.99,
            )
        raise AssertionError(f"Unexpected schema: {self.schema}")


class FakeModel:
    def with_structured_output(self, schema: type[Any], **_: Any) -> _StructuredFake:
        return _StructuredFake(schema)


def initial_state(question: str) -> dict[str, Any]:
    return {
        "request_id": "request-1",
        "question": question,
        "reports": [],
        "evidence_packets": [],
        "errors": [],
    }


def complete_technology_question() -> str:
    return "Our Cisco ISR4331 router has a connectivity failure; logs show interface resets."


def test_graph_routes_retrieves_verifies_and_synthesizes() -> None:
    evidence = Evidence(
        evidence_id="tech-1",
        content="Test-only evidence content.",
        source_title="Test Source",
        domain=Domain.TECHNOLOGY,
        organization="Cisco",
        page_number=1,
        score=0.9,
    )
    graph = build_consulting_graph(
        FakeModel(),
        InMemoryRetriever([evidence]),
        allow_model_router=False,
    )

    result = graph.invoke(initial_state(complete_technology_question()))

    assert result["route"].domains == [Domain.TECHNOLOGY]
    assert result["verification"].passed is True
    assert result["final_response"].request_id == "request-1"
    assert result["final_response"].citations[0].evidence_id == "tech-1"
    assert result["final_response"].confidence < 0.99


def test_graph_abstains_when_retrieval_is_empty() -> None:
    graph = build_consulting_graph(
        FakeModel(), NullRetriever(), allow_model_router=False
    )

    result = graph.invoke(initial_state(complete_technology_question()))

    assert result["verification"].passed is False
    assert result["final_response"].confidence == 0.0
    assert result["final_response"].recommendations == []


def test_graph_fans_out_to_two_selected_specialists() -> None:
    evidence = [
        Evidence(
            evidence_id="tech-1",
            content="Test-only technical evidence.",
            source_title="Technical Test Source",
            domain=Domain.TECHNOLOGY,
            organization="Cisco",
            score=0.9,
        ),
        Evidence(
            evidence_id="sec-1",
            content="Test-only filing evidence.",
            source_title="SEC Test Source",
            domain=Domain.SEC,
            organization="Cisco",
            score=0.85,
        ),
    ]
    graph = build_consulting_graph(
        FakeModel(), InMemoryRetriever(evidence), allow_model_router=False
    )

    result = graph.invoke(
        initial_state(
            "How do Cisco router outages affect the financial risks in its 10-K?"
        ),
        {"max_concurrency": 2},
    )

    assert set(result["route"].domains) == {Domain.TECHNOLOGY, Domain.SEC}
    assert {report.domain for report in result["reports"]} == {
        Domain.TECHNOLOGY,
        Domain.SEC,
    }
    assert len(result["reports"]) == 2
    assert result["verification"].passed is True


def test_graph_asks_for_clarification_when_domain_is_unknown() -> None:
    graph = build_consulting_graph(
        FakeModel(), NullRetriever(), allow_model_router=False
    )

    result = graph.invoke(initial_state("Help us make a better decision."))

    assert result["final_response"].selected_domains == []
    assert result["final_response"].clarification_questions
    assert "verification" not in result


def test_graph_pauses_for_missing_critical_technology_details() -> None:
    graph = build_consulting_graph(
        FakeModel(), NullRetriever(), allow_model_router=False
    )

    result = graph.invoke(
        initial_state("Our Cisco enterprise router has intermittent connectivity failures.")
    )

    assert result["route"].domains == [Domain.TECHNOLOGY]
    assert result["route"].clarification_required is True
    assert result["final_response"].selected_domains == [Domain.TECHNOLOGY]
    assert result["final_response"].clarification_questions
    assert "verification" not in result
