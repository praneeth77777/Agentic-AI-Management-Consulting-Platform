"""LangGraph manager, specialist fan-out, verification, and synthesis."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.router import RouterService
from app.agents.specialist import SpecialistService
from app.agents.synthesizer import SynthesisService, clarification_response
from app.agents.verifier import verify_reports
from app.graph.state import ConsultingState, SpecialistTask
from app.models import Domain
from app.retrieval import EvidenceRetriever


def build_consulting_graph(
    model: Any,
    retriever: EvidenceRetriever,
    *,
    top_k: int = 5,
    allow_model_router: bool = True,
):
    """Compile the consulting workflow around one shared model client."""
    router = RouterService(model, allow_model_fallback=allow_model_router)
    specialist = SpecialistService(model, retriever, top_k=top_k)
    synthesizer = SynthesisService(model)

    def manager_node(state: ConsultingState) -> dict[str, Any]:
        return {"route": router.route(state["question"])}

    def dispatch_specialists(state: ConsultingState):
        route = state["route"]
        if not route.domains or route.clarification_required:
            return "clarify"
        return [
            Send(
                "specialist",
                {
                    "request_id": state["request_id"],
                    "question": state["question"],
                    "domain": domain,
                },
            )
            for domain in route.required_specialists
        ]

    def specialist_node(state: SpecialistTask) -> dict[str, Any]:
        domain = Domain(state["domain"])
        try:
            report, evidence = specialist.analyze(state["question"], domain)
            return {"reports": [report], "evidence_packets": evidence}
        except Exception as exc:
            report = SpecialistService._empty_evidence_report(domain)
            return {
                "reports": [report],
                "errors": [
                    f"{domain.value} specialist failed: {type(exc).__name__}: {exc}"
                ],
            }

    def verification_node(state: ConsultingState) -> dict[str, Any]:
        return {
            "verification": verify_reports(
                state.get("reports", []), state.get("evidence_packets", [])
            )
        }

    def synthesis_node(state: ConsultingState) -> dict[str, Any]:
        return {
            "final_response": synthesizer.synthesize(
                request_id=state["request_id"],
                question=state["question"],
                route=state["route"],
                reports=state.get("reports", []),
                evidence=state.get("evidence_packets", []),
                verification=state["verification"],
            )
        }

    def clarification_node(state: ConsultingState) -> dict[str, Any]:
        return {
            "final_response": clarification_response(
                state["request_id"], state["route"]
            )
        }

    builder = StateGraph(ConsultingState)
    builder.add_node("manager", manager_node)
    builder.add_node("specialist", specialist_node)
    builder.add_node("verify_evidence", verification_node)
    builder.add_node("synthesize", synthesis_node)
    builder.add_node("clarify", clarification_node)

    builder.add_edge(START, "manager")
    builder.add_conditional_edges(
        "manager", dispatch_specialists, ["specialist", "clarify"]
    )
    builder.add_edge("specialist", "verify_evidence")
    builder.add_edge("verify_evidence", "synthesize")
    builder.add_edge("synthesize", END)
    builder.add_edge("clarify", END)
    return builder.compile()
