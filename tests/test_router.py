from app.agents.router import RouterService
from app.models import Domain


def route(question: str):
    return RouterService(None, allow_model_fallback=False).route(question)


def test_technology_failure_requires_critical_missing_information() -> None:
    decision = route("Our Cisco enterprise router has intermittent connectivity failures.")
    assert decision.domains == [Domain.TECHNOLOGY]
    assert decision.required_specialists == [Domain.TECHNOLOGY]
    assert decision.clarification_required is True
    assert "diagnostics" in " ".join(decision.missing_information).lower()


def test_complete_technology_failure_can_reach_specialist() -> None:
    decision = route(
        "Our Cisco ISR4331 router has a connectivity failure; logs show interface resets."
    )
    assert decision.domains == [Domain.TECHNOLOGY]
    assert decision.clarification_required is False


def test_routes_filing_and_router_question_to_two_domains() -> None:
    decision = route(
        "How do Cisco router outages affect the operational and financial risks in its 10-K?"
    )
    assert set(decision.domains) == {Domain.TECHNOLOGY, Domain.SEC}
    assert decision.intent == "cross_domain_analysis"
    assert decision.risk_level == "high"


def test_cisco_10k_risk_question_is_sec_only() -> None:
    decision = route("What risks did Cisco disclose in its 10-K?")
    assert decision.domains == [Domain.SEC]
    assert decision.entities == ["Cisco"]


def test_cisco_revenue_question_is_sec_only() -> None:
    decision = route("Summarize Cisco revenue and cash flow from the annual report.")
    assert decision.domains == [Domain.SEC]


def test_entity_name_alone_does_not_force_technology() -> None:
    decision = route("Tell me about Cisco.")
    assert decision.domains == []
    assert decision.clarification_required is True


def test_routes_food_security_to_corporate_responsibility() -> None:
    decision = route("Which sustainable technology investments could improve food security?")
    assert set(decision.domains) == {
        Domain.TECHNOLOGY,
        Domain.CORPORATE_RESPONSIBILITY,
    }


def test_unsupported_question_requests_clarification() -> None:
    decision = route("Please help us make a better decision.")
    assert decision.domains == []
    assert decision.missing_information
    assert decision.clarification_required is True
