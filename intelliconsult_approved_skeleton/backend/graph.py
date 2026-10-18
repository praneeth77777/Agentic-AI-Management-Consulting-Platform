"""Explicit LangGraph routing and specialist execution. No autonomous loops."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .contracts import ConsultReport, Domain, Finding, Evidence
from .retrieval import hybrid_retrieve
from .agents import specialist
from .recommend import synthesize
from .verify import verify
class State(TypedDict, total=False):
    question:str
    selected_agents:list[Domain]
    needs_clarification:bool
    missing_information:list[str]
    findings:list[Finding]
    evidence:list[Evidence]
    report:ConsultReport

def routing(question:str)->list[Domain]:
    q=question.lower()
    selected=[]
    groups={'technology':('router','cisco','cloud','network','server','ibm','google'),
      'clinical':('agilent','laboratory','instrument','diagnostic','clinical'),
      'sec':('financial','annual report','filing','supplier risk','investor','sec','risk'),
      'csr':('sustainability','food security','farming','csr','irrigation','food waste')}
    for domain,words in groups.items():
        if any(w in q for w in words):selected.append(domain)
    return selected

def manager_node(state: State):
    selected = routing(state['question'])
    if not selected:
        return {
            'selected_agents': [],
            'needs_clarification': True,
            'missing_information': [
                'Specify whether your question concerns technology, clinical equipment, SEC filings, or corporate responsibility, and describe the decision you need help making.'
            ],
        }
    return {'selected_agents': selected, 'needs_clarification': False, 'missing_information': []}

def after_manager(state: State) -> str:
    return 'clarification' if state.get('needs_clarification') else 'specialists'

def clarification_node(state: State):
    return {'report': ConsultReport(
        question=state['question'], selected_agents=[],
        needs_clarification=True,
        missing_information=state.get('missing_information', []),
        status='needs_clarification',
        findings=[], evidence=[], recommendations=[],
        uncertainties=['The question could not be assigned reliably to a supported consulting domain.'],
        risks=[], next_actions=['Clarify the topic and the business decision you want support with.'],
        kpis=[], mode='clarification',
    )}

def specialists_node(state: State):
    evidence=[];findings=[]
    for domain in state['selected_agents']:
        docs=hybrid_retrieve(state['question'],domain)
        evidence.extend(docs)
        findings.append(specialist(state['question'],domain,docs))
    return {'evidence':evidence,'findings':findings}


def report_node(state: State):

    findings = state["findings"]
    evidence = state["evidence"]

    # Step 1: Generate proposed recommendations.
    proposed = synthesize(findings, evidence)

    # Identify domains that use real document retrieval.
    real_domains = {
        e.domain for e in evidence
        if e.retrieval == "hybrid"
    }

    accepted = []
    withheld = []

    # Step 2: Review each recommendation individually.
    for recommendation in proposed:

        # Preserve existing illustrative mock recommendations.
        if recommendation.domain not in real_domains:
            accepted.append(recommendation)
            continue

        # Run existing evidence checks on this recommendation.
        problems = verify(
            [],
            [recommendation],
            evidence
        )

        # Conservative safeguard for the prototype:
        # Avoid definitive decisions before customer
        # requirements have been validated.
        action = recommendation.action.strip().lower()

        premature_actions = (
            "deploy ",
            "select ",
            "choose ",
            "purchase ",
            "buy ",
            "order ",
            "opt for ",
            "implement "
        )

        if action.startswith(premature_actions):
            problems.append(
                "A deployment or purchasing decision requires "
                "confirmed customer requirements and stronger validation."
            )

        if problems:
            withheld.append(
                f"Recommendation withheld for review: "
                f"{recommendation.action}. "
                f"Reasons: {'; '.join(problems)}"
            )
        else:
            accepted.append(recommendation)

    # Step 3: Verify findings and retained recommendations.
    issues = verify(findings, accepted, evidence)

    mock = any(
        e.retrieval == "mock"
        for e in evidence
    )

    uncertainties = []

    if mock:
        uncertainties.append(
            "Some document passages are synthetic demonstration data."
        )

    uncertainties.extend(issues)
    uncertainties.extend(withheld)

    if real_domains:
        uncertainties.append(
            "Automated evidence checks are heuristic and do not "
            "guarantee that every generated claim is factually supported."
        )

    next_actions = [
        "Confirm customer-specific constraints",
        "Review cited documents before committing funds"
    ]

    if withheld:
        next_actions.insert(
            0,
            "Review or regenerate withheld recommendations "
            "with stronger supporting evidence."
        )

    return {
        "report": ConsultReport(
            question=state["question"],
            selected_agents=state["selected_agents"],
            findings=findings,
            evidence=evidence,
            recommendations=accepted,
            uncertainties=uncertainties,
            risks=[
                "Recommendations are preliminary and must be "
                "checked against authoritative sources."
            ],
            next_actions=next_actions,
            kpis=[
                "Time to decision",
                "Recommendation validity"
            ],
            mode="mock" if mock else "hybrid"
        )
    }


def make_graph():
    graph=StateGraph(State)
    graph.add_node('manager',manager_node)
    graph.add_node('specialists',specialists_node)
    graph.add_node('report',report_node)
    graph.add_node('clarification',clarification_node)
    graph.add_edge(START,'manager')
    graph.add_conditional_edges('manager', after_manager, {'clarification':'clarification', 'specialists':'specialists'})
    graph.add_edge('clarification',END)
    graph.add_edge('specialists','report')
    graph.add_edge('report',END)
    return graph.compile()
_GRAPH=None
def consult(question:str)->ConsultReport:
    global _GRAPH
    if _GRAPH is None:_GRAPH=make_graph()
    state=_GRAPH.invoke({'question':question})
    return state['report']
