from __future__ import annotations

from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.router import route_question
from app.agents.specialist import run_specialist
from app.models.contracts import (
    ConsultingRecommendation,
    Domain,
    GraphState,
)
from app.recommendation.synthesize import synthesize
from app.recommendation.verify import verify_reports
from app.retrieval.service import HybridRetriever


_retriever: HybridRetriever | None = None


def retriever() -> HybridRetriever:
    global _retriever

    if _retriever is None:
        _retriever = HybridRetriever()

    return _retriever


def build_retrieval_query(
    question: str,
    domain: Domain,
) -> str:
    """
    Build a domain-aware retrieval query.

    The specialist still receives a focused natural-language question,
    while retrieval may use additional domain terminology to improve
    evidence ranking.
    """

    if domain == Domain.sec:
        return (
            f"{question} "
            "Item 1A Risk Factors "
            "operational risk cybersecurity third-party suppliers "
            "customer concentration litigation product defects "
            "regulatory risk financial condition"
        )

    return question


def build_specialist_question(
    question: str,
    domain: Domain,
    *,
    multi_domain: bool,
) -> str:
    """
    Produce a domain-isolated question for each specialist.

    For single-domain requests, preserve the user's original question.

    For multi-domain requests, prevent one specialist from reasoning
    about another specialist's domain. This keeps Technology, SEC,
    Clinical, and CSR analysis independent until the synthesis stage.
    """

    if not multi_domain:
        return question

    text = question.lower()

    if domain == Domain.technology:
        if "cisco" in text:
            return (
                "What Cisco technology and network modernization options "
                "are supported by the supplied Technology documents? "
                "Focus only on technology capabilities, architecture, "
                "SD-WAN, networking, security features, management, "
                "performance, and implementation considerations. "
                "Do not analyze SEC, clinical, or corporate responsibility "
                "issues."
            )

        return (
            "What technology modernization options are supported by the "
            "supplied Technology documents? Focus only on technology "
            "capabilities, architecture, infrastructure, security, "
            "performance, and implementation considerations. "
            "Do not analyze SEC, clinical, or corporate responsibility "
            "issues."
        )

    if domain == Domain.sec:
        company = ""

        if "cisco" in text:
            company = "Cisco "
        elif "alphabet" in text or "google" in text:
            company = "Alphabet "
        elif "agilent" in text:
            company = "Agilent "

        return (
            f"What material business, operational, cybersecurity, "
            f"regulatory, financial, supplier, and market risks are "
            f"disclosed in the supplied {company}SEC filings that could "
            f"influence management decisions? "
            f"Focus only on SEC filing evidence. "
            f"Do not analyze technology product capabilities, clinical "
            f"research, or corporate responsibility evidence."
        )

    if domain == Domain.clinical:
        if "covid" in text:
            clinical_topic = (
                "machine-learning approaches for COVID-19 detection, "
                "prediction, severity assessment, and clinical outcomes"
            )

        elif "diabetes" in text:
            clinical_topic = (
                "clinical and machine-learning evidence related to diabetes"
            )

        elif "heart" in text:
            clinical_topic = (
                "clinical and machine-learning evidence related to "
                "heart disease and heart-attack prediction"
            )

        elif "knee" in text:
            clinical_topic = (
                "clinical evidence related to knee injuries, "
                "rehabilitation, monitoring, and associated technologies"
            )

        else:
            clinical_topic = (
                "the clinical question supported by the supplied "
                "Clinical evidence"
            )

        return (
            f"What does the supplied Clinical evidence suggest about "
            f"{clinical_topic}? "
            f"Focus only on findings supported by clinical studies. "
            f"Do not connect the clinical evidence to Cisco network "
            f"modernization, SEC risks, or corporate responsibility "
            f"unless such a connection is explicitly supported by the "
            f"clinical evidence. "
            f"Do not provide diagnosis or treatment advice."
        )

    if domain == Domain.csr:
        return (
            "What corporate responsibility priorities are supported by "
            "the supplied food-security, nutrition, sustainability, and "
            "SOFI evidence? Focus only on food security, nutrition, "
            "development financing, sustainability, stakeholder "
            "coordination, and related corporate responsibility issues. "
            "Do not analyze Cisco technology, SEC filing risks, or "
            "clinical research."
        )

    return question


def route_node(
    state: GraphState,
) -> dict:
    route = route_question(
        state.question
    )

    return {
        "route": route,
    }


def specialists_node(
    state: GraphState,
) -> dict:
    route = state.route

    if route is None:
        raise ValueError(
            "Routing decision is missing from graph state."
        )

    if route.needs_clarification:
        return {
            "reports": [],
            "evidence": {},
        }

    reports = []
    evidence_by_domain = {}

    multi_domain = (
        len(route.required_specialists) > 1
    )

    for domain in route.required_specialists:
        specialist_question = build_specialist_question(
            state.question,
            domain,
            multi_domain=multi_domain,
        )

        retrieval_query = build_retrieval_query(
            specialist_question,
            domain,
        )

        evidence = retriever().search(
            retrieval_query,
            domain,
            k=5,
        )

        evidence_by_domain[
            domain.value
        ] = evidence

        report = run_specialist(
            domain=domain,
            question=specialist_question,
            evidence=evidence,
        )

        reports.append(
            report
        )

    return {
        "reports": reports,
        "evidence": evidence_by_domain,
    }


def verify_node(
    state: GraphState,
) -> dict:
    verification = verify_reports(
        state.reports,
        state.evidence,
    )

    return {
        "verification": verification,
    }


def synthesize_node(
    state: GraphState,
) -> dict:
    route = state.route

    if route is None:
        raise ValueError(
            "Routing decision is missing from graph state."
        )

    if route.needs_clarification:
        recommendation = ConsultingRecommendation(
            executive_summary=(
                "I need critical information before making a "
                "supported recommendation."
            ),
            selected_domains=route.domains,
            uncertainty=[
                item
                for item in route.missing_information
            ],
            next_actions=[
                f"Provide: {item}"
                for item in route.missing_information
            ],
            confidence=0.0,
        )

        return {
            "recommendation": recommendation,
        }

    if state.verification is None:
        raise ValueError(
            "Verification result is missing from graph state."
        )

    evidence = [
        item
        for items in state.evidence.values()
        for item in items
    ]

    recommendation = synthesize(
        state.question,
        state.reports,
        evidence,
        state.verification,
    )

    return {
        "recommendation": recommendation,
    }


def build_graph():
    graph_builder = StateGraph(
        GraphState
    )

    graph_builder.add_node(
        "route",
        route_node,
    )

    graph_builder.add_node(
        "specialists",
        specialists_node,
    )

    graph_builder.add_node(
        "verify",
        verify_node,
    )

    graph_builder.add_node(
        "synthesize",
        synthesize_node,
    )

    graph_builder.add_edge(
        START,
        "route",
    )

    graph_builder.add_edge(
        "route",
        "specialists",
    )

    graph_builder.add_edge(
        "specialists",
        "verify",
    )

    graph_builder.add_edge(
        "verify",
        "synthesize",
    )

    graph_builder.add_edge(
        "synthesize",
        END,
    )

    return graph_builder.compile()


graph = build_graph()


def new_state(
    question: str,
) -> dict:
    state = GraphState(
        request_id=str(
            uuid4()
        ),
        question=question,
    )

    return state.model_dump()