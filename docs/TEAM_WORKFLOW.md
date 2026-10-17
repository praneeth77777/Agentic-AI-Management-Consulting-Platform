# Team Workflow

## Proposed Ownership

Replace Member 1-4 with names after the team agrees.

| Owner | Primary responsibility | Expected output |
|---|---|---|
| Member 1 | Repository, environment, ingestion | Reproducible setup and parsed documents |
| Member 2 | Hybrid retrieval, citations, ranking | Retrieval service and retrieval evaluation |
| Member 3 | LangGraph Manager, Technology, SEC | Routing and first cross-domain workflow |
| Member 4 | Clinical, Corporate Responsibility, API, UI | Remaining specialists and demonstration application |

Evaluation, testing, presentation, and documentation are shared responsibilities.

## First Two Hours

1. Create the private repository.
2. Add this documentation pack.
3. Invite all team members.
4. Create the initial GitHub issues.
5. Verify Python and Git on every computer.
6. Install Ollama on the M4 Max integration computer.
7. Test one local model and one embedding model.
8. Record results in `docs/HANDOFF.md`.

## Twenty Four Hour Schedule

| Hours | Focus | Exit condition |
|---|---|---|
| 0-2 | Repository and environment | All members can clone; local model responds |
| 2-5 | Data inventory and ingestion | Technology and SEC samples parse with metadata |
| 5-8 | Hybrid retrieval | Vector and keyword results contain citations |
| 8-11 | Manager, Technology, SEC | First two agents return validated reports |
| 11-13 | Cross-domain integration | Technology and SEC synthesis works |
| 13-16 | Clinical and Corporate Responsibility | Four agents route and retrieve |
| 16-18 | FastAPI and Streamlit | End-to-end application works |
| 18-21 | Evaluation | Metrics and failures recorded |
| 21-24 | Stabilization and presentation | Demo rehearsed and documentation current |

## GitHub Issues

Create these issues first:

1. Repository and cross-platform environment
2. Data catalog and ingestion pipeline
3. Chroma and SQLite FTS5 retrieval
4. Evidence packet and citation model
5. LangGraph state and Manager router
6. Technology Agent
7. SEC Agent
8. Technology and SEC cross-domain workflow
9. Clinical Agent
10. Corporate Responsibility Agent
11. Recommendation ranking and verifier
12. FastAPI endpoints
13. Streamlit interface
14. Evaluation dataset and metrics
15. Demonstration script and presentation

## Pull Request Checklist

- [ ] The pull request addresses one issue.
- [ ] Relevant tests pass.
- [ ] No credentials or course data are committed.
- [ ] Error and empty-result behavior is covered.
- [ ] Documentation is updated.
- [ ] `docs/HANDOFF.md` names the next task.
- [ ] Another teammate reviewed the change.

## Handoff Rule

No teammate should say “it works on my laptop” without committing the code, documenting the command, and recording the test result. If work cannot be committed, record exactly where it exists and why, then transfer it through an approved team channel immediately.

