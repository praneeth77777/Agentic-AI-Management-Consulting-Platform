# Agentic AI Management Consulting Platform

This repository is for the CMPE 256 Data Science Hackathon. The goal is to build a local, evidence-grounded multi-agent consulting prototype that converts enterprise questions into cited recommendations, risks, next actions, and measurable outcomes.

## Selected Architecture

```text
Streamlit
   |
FastAPI
   |
LangGraph Manager and Router
   |
   +-- Technology Agent
   +-- Clinical Agent
   +-- SEC Agent
   `-- Corporate Responsibility Agent
            |
Hybrid Retrieval and Recommendation Ranking
            |
Chroma + SQLite FTS5 + Supplied Documents
            |
Evidence Verification and Consulting Response
```

All agents share one Ollama model. The Manager invokes only the specialists required for a question.

## Current State

Planning and architecture are complete. Application implementation has not started. See `START_HERE.md` and `docs/HANDOFF.md` for the authoritative status.

## Repository Layout

```text
agentic-consulting-platform/
|-- START_HERE.md
|-- AGENTS.md
|-- README.md
|-- .env.example
|-- .gitignore
|-- app/
|   |-- api/
|   |-- agents/
|   |-- graph/
|   |-- retrieval/
|   |-- recommendation/
|   |-- models/
|   `-- ui/
|-- tests/
|-- evaluation/
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- indexes/
`-- docs/
```

## Documentation

- `START_HERE.md` - entry point for a new person or AI account
- `AGENTS.md` - stable repository instructions
- `docs/HANDOFF.md` - current work state and next task
- `docs/PROJECT_STATUS.md` - implementation checklist
- `docs/DECISIONS.md` - architecture decisions
- `docs/ARCHITECTURE.md` - component and workflow design
- `docs/DATA_CATALOG.md` - supplied data inventory and ingestion status
- `docs/EVALUATION_PLAN.md` - metrics and test cases
- `docs/TEAM_WORKFLOW.md` - team responsibilities and Git workflow

## Setup

Setup commands will be added after the repository structure and dependency files are created. Do not invent commands or mark setup complete until they have been tested on both macOS and Windows.

## Security

The original course files, credentials, local models, vector indexes, `.env`, and generated databases must remain outside Git unless the professor explicitly authorizes them.

