from app.agents.router import route_question
from app.models.contracts import Domain

def test_technology_route():
    r = route_question("What should I check on a Cisco Catalyst router?")
    assert Domain.technology in r.domains
    assert Domain.sec not in r.domains

def test_cross_domain_route():
    r = route_question("What Cisco infrastructure decision is affected by risks disclosed in its SEC filing?")
    assert set(r.domains) == {Domain.technology, Domain.sec}

def test_missing_model_clarification():
    r = route_question("Which replacement part is compatible with my broken Cisco router?")
    assert r.needs_clarification
    assert "Exact product/model identifier" in r.missing_information
