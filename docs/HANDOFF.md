# Current Project Handoff

**Last updated:** October 18, 2026  
**Current phase:** MVP implementation complete; final evaluation/demo stabilization

## Objective

Build a zero-cost local Agentic AI Management Consulting Platform that routes enterprise questions to specialized agents, retrieves evidence from supplied documents, verifies support, and produces cited consulting recommendations with risks, uncertainty, next actions, and KPIs.

## Approved Stack

- Python 3.11
- LangGraph for orchestration
- Ollama for local inference
- FastAPI backend
- Streamlit interface
- Chroma vector retrieval
- SQLite FTS5 keyword retrieval
- Pydantic structured contracts
- pytest automated tests

All specialist agents share one local Ollama model.

## Implemented Architecture

The working flow is:

```text
Streamlit
  -> FastAPI
  -> LangGraph Manager / Router
      -> Technology Agent
      -> SEC Agent
      -> Clinical Agent
      -> Corporate Responsibility Agent
  -> Hybrid Retrieval
      -> Chroma semantic search
      -> SQLite FTS5 keyword search
      -> reranking
  -> Evidence Verifier
  -> Recommendation Synthesizer
  -> Final Consulting Recommendation