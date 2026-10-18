
---

## `AGENTS.md`

```markdown
# Repository Instructions for AI Coding Agents

## Objective

Maintain the Agentic AI Management Consulting Platform.

The system routes enterprise questions to specialized agents, retrieves domain evidence, verifies support, and produces structured recommendations.

## Approved Stack

- Python 3.11
- LangGraph
- Ollama
- FastAPI
- Streamlit
- Chroma
- SQLite FTS5
- Pydantic
- pytest

Do not introduce Azure services, paid APIs, or a different orchestration framework without a new architecture decision.

## Implemented Agents

- Manager / Router
- Technology Agent
- SEC Agent
- Clinical Agent
- Corporate Responsibility Agent

All specialists use the same Ollama model.

## Multi-Domain Behavior

For multi-domain questions, specialists receive domain-specific questions.

This prevents cross-domain contamination before final synthesis.

## Coding Rules

- keep the system a modular monolith
- use Pydantic models for structured contracts
- keep retrieval logic outside prompts
- preserve evidence metadata
- use stable evidence IDs
- reject unsupported evidence IDs
- separate findings, assumptions, missing information, recommendations, and risks
- add or update tests when behavior changes
- do not redesign working architecture without a documented reason

## Safety

Clinical and SEC workflows require human review.

The system is decision support only.

Never fabricate:

- citations
- clinical results
- financial facts
- product capabilities
- compatibility claims

## Repository Safety

Never commit:

- passwords
- API keys
- tokens
- `.env`
- Ollama model files
- supplied PDFs
- supplied CSVs
- `data/raw/`
- `data/indexes/`
- Chroma databases
- generated SQLite databases

## Current Status

Core MVP implementation is complete.

Latest automated test result:

```text
8 passed, 1 warning