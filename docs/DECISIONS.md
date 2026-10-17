# Architecture Decisions

Do not delete superseded decisions. Add a new decision and link it to the previous one.

## ADR-001 Local First Zero Cost Prototype

**Date:** October 17, 2026  
**Status:** Accepted

### Decision

Run the prototype locally and avoid paid inference or cloud dependencies.

### Reason

The team has no remaining paid API credits and must produce a reproducible demonstration without personal expense. The M4 Max integration computer has 48 GB unified memory and can host one shared local model.

### Consequences

- Ollama will provide model inference.
- All agents share one model.
- The demonstration can run on one integration computer.
- Cloud deployment remains future work.

## ADR-002 LangGraph as Primary Orchestrator

**Date:** October 17, 2026  
**Status:** Accepted  
**Supersedes:** Earlier planning documents that selected Microsoft Agent Framework

### Decision

Use LangGraph for the hackathon implementation.

### Reason

The professor allowed any feasible framework. LangGraph has direct Ollama integrations, course examples, a larger supporting ecosystem, and explicit graph control suitable for a 24-hour prototype.

### Alternatives

- Microsoft Agent Framework
- Custom Python state machine
- AutoGen

### Consequences

- Do not implement two orchestration frameworks.
- Preserve framework-independent agent and retrieval contracts.
- Present Microsoft Agent Framework as an evaluated alternative and possible future migration path.

## ADR-003 Modular Monolith

**Date:** October 17, 2026  
**Status:** Accepted

### Decision

Run the UI, API, orchestration, retrieval, and agents as modules in one Python repository.

### Reason

Separate microservices add setup, networking, deployment, and debugging work without improving the academic demonstration.

### Consequences

- FastAPI remains the external application boundary.
- Internal modules retain clear interfaces for later extraction.
- No RabbitMQ, Kubernetes, or service mesh in the prototype.

## ADR-004 Two Specialist Agents Before Four

**Date:** October 17, 2026  
**Status:** Accepted

### Decision

Implement and integrate Technology and SEC first. After the shared pattern works, add Clinical and Corporate Responsibility using the same specialist contract.

### Reason

Technology and SEC share Cisco and Agilent entities and provide a meaningful cross-domain consulting scenario. The professor recommended proving two SME integrations before expanding to four.

### Consequences

- All four agents remain in the target architecture.
- Shared code must make the third and fourth agents configuration additions rather than new systems.

## ADR-005 Hybrid Retrieval

**Date:** October 17, 2026  
**Status:** Accepted

### Decision

Combine Chroma semantic search with SQLite FTS5 keyword search and rerank the merged results.

### Reason

Technical identifiers, product names, filing terms, and medical terminology benefit from exact search, while explanatory questions benefit from semantic search.

### Consequences

- Preserve metadata in both indexes.
- Measure retrieval results separately and after fusion.
- Cite the final supporting chunks.

