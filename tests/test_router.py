from app.agents.router import route_question
from app.models.contracts import Domain


def test_sec_only_cisco_question():
    route = route_question(
        "What operational risks does Cisco disclose "
        "in the supplied SEC filings?"
    )

    assert route.domains == [Domain.sec]
    assert route.required_specialists == [Domain.sec]
    assert "Cisco" in route.extracted_entities


def test_technology_only_cisco_question():
    route = route_question(
        "What capabilities does Cisco Catalyst infrastructure provide?"
    )

    assert route.domains == [Domain.technology]


def test_cross_domain_cisco_question():
    route = route_question(
        "What Cisco technology modernization actions should management "
        "consider, and what risks disclosed in Cisco SEC filings should "
        "influence the decision?"
    )

    assert Domain.technology in route.domains
    assert Domain.sec in route.domains