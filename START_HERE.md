
---

## `START_HERE.md`

```markdown
# Start Here

## Project

**Course:** CMPE 256  
**Project:** Agentic AI Management Consulting Platform  
**Status:** Core MVP implementation complete

## Objective

Build a zero-cost local Agentic AI Management Consulting Platform that:

1. routes enterprise questions to specialist agents,
2. retrieves supporting evidence,
3. verifies evidence,
4. produces structured consulting recommendations.

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

Microsoft Agent Framework, Azure OpenAI, and Azure AI Foundry are not part of the initial prototype.

## Implemented Agents

- Manager / Router
- Technology Agent
- SEC Agent
- Clinical Agent
- Corporate Responsibility Agent

All specialists share one local Ollama model.

## Current Status

- [x] Development environment configured
- [x] Ollama configured
- [x] Technology data ingested
- [x] SEC data ingested
- [x] Clinical data ingested
- [x] Corporate Responsibility data ingested
- [x] Hybrid retrieval implemented
- [x] Manager/router implemented
- [x] Technology Agent implemented
- [x] SEC Agent implemented
- [x] Clinical Agent implemented
- [x] Corporate Responsibility Agent implemented
- [x] Evidence verification implemented
- [x] Recommendation synthesis implemented
- [x] FastAPI implemented
- [x] Streamlit implemented
- [x] Technology + SEC workflow validated
- [x] Full four-domain workflow validated
- [x] Automated tests passing
- [ ] Formal evaluation completed
- [ ] Final demo rehearsal completed

## Indexed Data

| Domain | Chunks |
|---|---:|
| Technology | 219 |
| SEC | 2,376 |
| Clinical | 14,990 |
| Corporate Responsibility | 1,590 |

## Latest Test Result

```text
8 passed, 1 warning