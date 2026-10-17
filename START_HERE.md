# Start Here

This file is the entry point for every teammate and every new AI coding session.

## Project

**Course:** CMPE 256 Recommender Systems  
**Challenge:** Data Science Hackathon - Agentic AI Management Consulting Platform  
**Team size:** Four  
**Current date:** October 17, 2026  
**Current phase:** Planning complete; implementation has not started

The Market Basket Recommendation challenge is outside this repository's scope.

## Current Decision

Build a zero-cost local prototype with this stack:

- Streamlit web interface
- FastAPI backend
- LangGraph orchestration
- Ollama local model inference
- Chroma vector retrieval
- SQLite FTS5 keyword retrieval
- SentenceTransformers or Ollama embeddings
- Supplied hackathon documents and datasets
- GitHub for source control and project continuity

The professor said the team may choose whatever is feasible. Azure OpenAI, Azure AI Foundry, and Microsoft Agent Framework are not mandatory. Microsoft Agent Framework was evaluated but is no longer the selected implementation framework.

## Target Architecture

One Manager node routes requests to four Subject Matter Expert agents:

1. Technology Agent
2. Clinical Agent
3. SEC Agent
4. Corporate Responsibility Agent

All four agents share one Ollama model. Each agent has its own instructions, retrieval filter or collection, and structured output contract. Do not load a separate model for each agent.

Implement Technology and SEC first, prove one cross-domain workflow, and then reuse the same specialist contract for Clinical and Corporate Responsibility.

## Current Status

- [x] Hackathon materials collected
- [x] Requirements and data sources reviewed
- [x] Zero-cost local approach selected
- [x] LangGraph selected as the primary orchestrator
- [x] Manager-and-specialist architecture selected
- [x] Four-agent expansion strategy selected
- [ ] GitHub repository created
- [ ] Development environments configured
- [ ] Ollama installed and model selected
- [ ] Documents ingested
- [ ] Retrieval implemented
- [ ] LangGraph workflow implemented
- [ ] FastAPI implemented
- [ ] Streamlit implemented
- [ ] Evaluation dataset created
- [ ] End-to-end demonstration completed

No application implementation has been completed yet. Do not claim otherwise.

## Read Order

Read these files before proposing or changing code:

1. `START_HERE.md`
2. `AGENTS.md`
3. `docs/HANDOFF.md`
4. `docs/PROJECT_STATUS.md`
5. `docs/DECISIONS.md`
6. `docs/ARCHITECTURE.md`
7. `docs/DATA_CATALOG.md`
8. `docs/EVALUATION_PLAN.md`
9. `docs/TEAM_WORKFLOW.md`
10. `README.md`

Then inspect the repository:

```bash
git status
git branch --show-current
git log --oneline -10
```

Inspect existing code and tests before suggesting new files or redesigning the architecture.

## Source of Truth Order

When information conflicts, use this order:

1. Current code and passing tests
2. `docs/HANDOFF.md`
3. `docs/PROJECT_STATUS.md`
4. `docs/DECISIONS.md`
5. `docs/ARCHITECTURE.md`
6. Older reports, presentations, chat messages, and planning documents

Older documents that select Microsoft Agent Framework are superseded by decision ADR-002 in `docs/DECISIONS.md`.

## Prompt for a New ChatGPT Account

Copy the following prompt into a new account after attaching this pack or granting access to the GitHub repository:

```text
You are joining an existing four-person CMPE 256 hackathon project.

Do not redesign or implement anything yet.

Read START_HERE.md and AGENTS.md first. Then read the files listed in the
Read Order section of START_HERE.md. Inspect the current Git branch, recent
commits, working tree, application files, tests, and open issues.

Report:
1. The project objective
2. The approved architecture and technology stack
3. What has been completed
4. What currently works and which tests prove it
5. Work that is incomplete
6. Current blockers and risks
7. The next highest-priority GitHub issue
8. Any contradiction between the documentation and repository

Do not modify files until you present this summary and receive confirmation.
Do not restart completed work. Do not change the selected framework without
recording a new architecture decision.
```

## Required Session Closeout

Before any teammate or AI session stops:

1. Run relevant tests.
2. Update `docs/HANDOFF.md`.
3. Update `docs/PROJECT_STATUS.md`.
4. Update `docs/DECISIONS.md` if an architectural decision changed.
5. Update `docs/DATA_CATALOG.md` if data was added or processed.
6. Commit code, tests, and documentation together.
7. Push the branch.
8. Record the next task and remaining blocker.

Uncommitted work on one laptop is not part of the shared project.

