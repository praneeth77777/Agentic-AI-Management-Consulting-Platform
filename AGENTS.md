# Repository Instructions for AI Coding Agents

## Objective

Build a working prototype of an Agentic AI Management Consulting Platform that routes enterprise questions to specialized domain agents, retrieves authoritative evidence, ranks recommendations, cites sources, states uncertainty, and recommends measurable next actions.

## Scope

The repository contains only the Agentic AI Management Consulting Platform challenge. Do not implement the separate Market Basket Recommendation challenge.

## Approved Stack

- Python 3.11
- LangGraph for orchestration
- Ollama for local model inference
- FastAPI for the backend API
- Streamlit for the demonstration interface
- Chroma for vector retrieval
- SQLite FTS5 for keyword retrieval
- Pydantic for validated state and output contracts
- pytest for automated tests

Do not introduce Azure services, paid APIs, Kubernetes, RabbitMQ, Redis, separate microservices, or another orchestration framework without an approved architecture decision.

## Agent Design

The workflow contains:

- Manager and routing node
- Technology specialist
- Clinical specialist
- SEC specialist
- Corporate Responsibility specialist
- Evidence verifier
- Recommendation synthesizer

Use one shared local model client. Agents differ through instructions, retrieval scope, tools, and structured output—not separate model processes.

Default to deterministic routing rules plus structured model classification. The workflow must request clarification when required entities or diagnostics are missing.

## Implementation Order

1. Repository and environment setup
2. Document inventory and ingestion
3. Hybrid retrieval and citations
4. Shared specialist input and output contracts
5. Technology and SEC agents
6. Technology and SEC cross-domain workflow
7. Clinical and Corporate Responsibility agents
8. Evidence verification and recommendation ranking
9. FastAPI and Streamlit integration
10. Evaluation and demonstration stabilization

## Coding Rules

- Keep the initial system a modular monolith.
- Keep domain behavior in configuration and prompts when practical.
- Use typed Pydantic models at workflow boundaries.
- Keep retrieval logic outside prompts.
- Preserve document title, page, section, domain, organization, date, and source path in metadata.
- Return evidence identifiers rather than unsupported prose claims.
- Distinguish facts, hypotheses, missing information, recommendations, risks, and next actions.
- Do not expose hidden chain-of-thought. Log workflow events, routing decisions, evidence IDs, scores, latency, and verification outcomes.
- Use small, reviewable functions and descriptive names.
- Add tests with every behavior change.

## Safety Rules

- The system is decision support, not an autonomous purchasing, clinical, financial, or regulatory authority.
- Never fabricate compatibility, diagnosis, financial facts, or citations.
- Clinical and financial recommendations must state limitations and require human review.
- Do not execute purchases, trades, diagnoses, treatment decisions, or external actions.
- Abstain when evidence is insufficient or conflicting.

## Data and Secrets

- Do not commit supplied course PDFs, CSV files, extracted text, model files, vector indexes, or generated databases unless the professor explicitly permits it.
- Do not commit `.env`, credentials, API keys, tokens, or account information.
- Commit `.env.example` only.
- Keep generated data under ignored directories.
- Record every source and ingestion result in `docs/DATA_CATALOG.md`.

## Git Workflow

- Work from one GitHub issue per branch.
- Use short branches such as `feat/retrieval`, `feat/technology-agent`, or `test/routing-evaluation`.
- Pull before starting work.
- Do not overwrite another teammate's changes.
- Run relevant tests before committing.
- Update handoff and status files in the same commit as the code change.
- Do not merge a branch with failing tests or undocumented blockers.

## Definition of Done for a Task

A task is complete only when:

- The requested behavior works.
- Relevant automated tests pass.
- Errors and empty results are handled.
- New configuration is documented.
- `docs/HANDOFF.md` and `docs/PROJECT_STATUS.md` are current.
- The branch is pushed and ready for review.

## Session Start

Before editing:

1. Read `START_HERE.md`.
2. Read `docs/HANDOFF.md` and `docs/PROJECT_STATUS.md`.
3. Inspect the current branch and recent commits.
4. Run the existing tests that cover the assigned component.
5. State the exact issue being handled and files likely to change.

## Session End

Before stopping:

1. Run tests.
2. Update the current-status documents.
3. Record commands and results in `docs/HANDOFF.md`.
4. Record unresolved failures exactly.
5. Commit and push.
6. Leave one clear next action.

