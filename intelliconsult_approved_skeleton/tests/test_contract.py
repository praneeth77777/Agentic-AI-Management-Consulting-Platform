from backend.graph import consult, routing
from backend.retrieval import mock_retrieve
from backend.recommend import synthesize
from backend.verify import verify
from backend.contracts import Finding

def test_routing():
    assert routing('Cisco router outage')==['technology']
    assert routing('Agilent laboratory instrument and financial supplier risk')==['clinical','sec']
    assert routing('What is the weather tomorrow?')==[]
def test_mock_evidence():
    doc=mock_retrieve('test','sec')[0]
    assert doc.source and doc.page==1 and doc.retrieval=='mock'
def test_consult_report():
    report=consult('Cisco router outage')
    assert report.selected_agents==['technology']
    assert report.mode=='mock'
    assert report.recommendations
    assert all('mock-' in x.id for x in report.evidence)
def test_verifier_invalid_id():
    f=Finding(domain='sec',summary='x',evidence_ids=['nonexistent'])
    assert verify([f],[],mock_retrieve('x','sec'))
def test_no_fabricated_score():
    findings=[Finding(domain='technology',summary='x',evidence_ids=['mock-technology-1'])]
    recs=synthesize(findings,mock_retrieve('x','technology'))
    assert all(r.score is None for r in recs)


def test_unmatched_question_requests_clarification():
    report = consult('What is the weather tomorrow?')
    assert report.selected_agents == []
    assert report.needs_clarification is True
    assert report.status == 'needs_clarification'
    assert report.missing_information
    assert report.findings == []
    assert report.evidence == []
    assert report.recommendations == []
    assert report.mode == 'clarification'

def test_matched_question_remains_normal():
    report = consult('Cisco router outage')
    assert report.selected_agents == ['technology']
    assert report.needs_clarification is False
    assert report.missing_information == []
    assert report.status == 'completed'
