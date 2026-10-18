from __future__ import annotations
from uuid import uuid4
from langgraph.graph import StateGraph, START, END
from app.models.contracts import GraphState, Domain
from app.agents.router import route_question
from app.agents.specialist import run_specialist
from app.retrieval.service import HybridRetriever
from app.recommendation.verify import verify_reports
from app.recommendation.synthesize import synthesize

_retriever: HybridRetriever | None = None

def retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever

def route_node(state: dict):
    route = route_question(state["question"])
    return {"route": route}

def specialists_node(state: dict):
    route = state["route"]
    if route.needs_clarification:
        return {"reports": [], "evidence": {}}
    reports, ev_map = [], {}
    for domain in route.required_specialists:
        ev = retriever().search(state["question"], domain, k=5)
        ev_map[domain.value] = ev
        reports.append(run_specialist(domain, state["question"], ev))
    return {"reports": reports, "evidence": ev_map}

def verify_node(state: dict):
    return {"verification": verify_reports(state.get("reports", []), state.get("evidence", {}))}

def synthesize_node(state: dict):
    route = state["route"]
    if route.needs_clarification:
        from app.models.contracts import ConsultingRecommendation
        rec = ConsultingRecommendation(
            executive_summary="I need critical information before making a supported recommendation.",
            selected_domains=route.domains, uncertainty=route.missing_information,
            next_actions=[f"Provide: {x}" for x in route.missing_information], confidence=0.0
        )
        return {"recommendation": rec}
    evidence = [e for items in state.get("evidence", {}).values() for e in items]
    return {"recommendation": synthesize(state["question"], state.get("reports", []), evidence, state["verification"])}

def build_graph():
    g = StateGraph(dict)
    g.add_node("route", route_node)
    g.add_node("specialists", specialists_node)
    g.add_node("verify", verify_node)
    g.add_node("synthesize", synthesize_node)
    g.add_edge(START, "route")
    g.add_edge("route", "specialists")
    g.add_edge("specialists", "verify")
    g.add_edge("verify", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

graph = build_graph()

def new_state(question: str) -> dict:
    return GraphState(request_id=str(uuid4()), question=question).model_dump()
