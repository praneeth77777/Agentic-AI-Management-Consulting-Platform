"""Command-line entry point for the first working prototype."""
"""To inspect graph: python -m app.cli --show-graph """
"""When running python -m app.cli "Our Cisco router is failing."
    it:
    1. Reads configuration.
    2. Selects a retriever.
        - If EVIDENCE_JSONL is set: JsonlKeywordRetriever(settings.evidence_jsonl)
        - If EVIDENCE_JSONL is not set: NullRetriever()
    3. Creates the Ollama model client.
    4. Builds the LangGraph workflow.
    5. Generates a request ID.
    6. sends the question through the graph.
    7. Prints the final response as JSON.
"""
from __future__ import annotations

import argparse
from uuid import uuid4

from app.config import Settings
from app.graph import build_consulting_graph
from app.retrieval import JsonlKeywordRetriever, NullRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local consulting LangGraph")
    parser.add_argument("question", nargs="?", help="Customer consulting question")
    parser.add_argument(
        "--show-graph", action="store_true", help="Print the graph as Mermaid text"
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    retriever = (
        JsonlKeywordRetriever(settings.evidence_jsonl)
        if settings.evidence_jsonl
        else NullRetriever()
    )

    if args.show_graph:
        graph = build_consulting_graph(
            object(), retriever, top_k=settings.retrieval_top_k
        )
        print(graph.get_graph().draw_mermaid())
        return

    from app.llm import create_ollama_model

    model = create_ollama_model(settings)
    graph = build_consulting_graph(
        model, retriever, top_k=settings.retrieval_top_k
    )

    question = args.question or input("Customer question: ").strip()
    if not question:
        parser.error("A non-empty question is required")

    result = graph.invoke(
        {
            "request_id": str(uuid4()),
            "question": question,
            "reports": [],
            "evidence_packets": [],
            "errors": [],
        },
        {"max_concurrency": settings.max_concurrency},
    )
    print(result["final_response"].model_dump_json(indent=2))


if __name__ == "__main__":
    main()

