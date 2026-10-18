# Agentic AI Management Consulting Platform

CMPE 256 hackathon project.

This project implements a local Agentic AI Management Consulting Platform that routes enterprise questions to specialized agents, retrieves supporting evidence, verifies citations, and produces structured consulting recommendations.

## Technology Stack

- Python 3.11
- LangGraph
- Ollama
- FastAPI
- Streamlit
- Chroma
- SQLite FTS5
- Pydantic
- pytest

Local models:

- `qwen2.5:7b`
- `nomic-embed-text`

## Architecture

```text
Streamlit
    |
FastAPI
    |
LangGraph Manager / Router
    |
    +-- Technology Agent
    +-- SEC Agent
    +-- Clinical Agent
    +-- Corporate Responsibility Agent
            |
      Hybrid Retrieval
     Chroma + SQLite FTS5
            |
      Evidence Verifier
            |
 Recommendation Synthesizer
            |
   Final Recommendation