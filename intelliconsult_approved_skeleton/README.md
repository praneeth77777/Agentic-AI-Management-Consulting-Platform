# IntelliConsult AI — Approved Architecture Skeleton

This is a **runnable, contract-first architecture skeleton**, not a finished AI consulting platform. Defaults are **MOCK** retrieval and agent responses. The recommendation synthesizer returns *unranked illustrative actions* until verified candidate data and criteria are provided. The evidence verifier currently checks citation IDs only; it does **not** prove semantic support.

## Approved architecture

Streamlit → FastAPI → LangGraph Manager → Technology/Clinical/SEC/CSR specialist → Chroma + SQLite FTS5 hybrid retrieval → Evidence verifier → Recommendation synthesizer → Report.

One shared local Ollama model can be enabled for domain summaries; the default does not require Ollama. LangGraph is actually used even in mock mode. Explicit graph transitions and deterministic multi-domain routing are used to avoid autonomous loops. Unmatched questions take a clarification branch, never a default Technology route. Hybrid retrieval fuses Chroma and SQLite FTS5 rankings with RRF.

## Quick start (Windows PowerShell, Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Launch the API in **terminal 1**:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Launch the UI in **terminal 2**:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Open http://localhost:8501. API Swagger: http://localhost:8000/docs.

## Move from mocks to local datasets

1. Place PDFs/TXT files under `data/technology`, `data/clinical`, `data/sec`, `data/csr`.
2. Index them (requires internet on the **first model download**, then works offline after caching):

```powershell
.\.venv\Scripts\python.exe -m backend.ingest
```

3. Stop and restart API in the same PowerShell terminal after setting:

```powershell
$env:RETRIEVAL_MODE='hybrid'
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

4. For real *local* Ollama summaries (install Ollama and `ollama pull qwen3:1.7b` first):

```powershell
$env:RETRIEVAL_MODE='hybrid'
$env:AGENT_MODE='ollama'
$env:OLLAMA_MODEL='qwen3:1.7b'
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

If all four collections are empty, the retriever may return no passages. **Check source coverage before expecting useful answers.** If Ollama is not available, mock mode still works.

## Ownership and migration points

- `backend/contracts.py`: shared Pydantic inputs/outputs. Finalize schemas before parallel changes.
- `backend/ingest.py`: PDF/TXT extraction, chunks, stable IDs, SQLite FTS5 and Chroma indexes.
- `backend/retrieval.py`: `hybrid_retrieve(question,domain)` (mock default; real hybrid optional).
- `backend/agents.py`: four specialist prompts; mock response or locally invoked Ollama.
- `backend/graph.py`: LangGraph Manager, domain routes, report generation.
- `backend/verify.py`: currently only checks citation identifiers; must add grounded entailment/faithfulness checks.
- `backend/recommend.py`: illustrative action synthesis; replace with candidate sourcing, hard constraints, domain-specific weights and justified ranking.
- `backend/main.py`: FastAPI `/health` and `/consult`.
- `frontend/app.py`: Streamlit report visualization.
- `tests/test_contract.py`: baseline smoke tests.

## Security

Never commit professor-provided datasets, extracted text, embeddings, indexes, SQLite databases, model files, or secrets to GitHub without explicit permission. `.gitignore` excludes these by default. This is intended for **local development** and should not be deployed publicly as-is.

## Important limitations

- Deterministic keyword routing is only a minimal baseline, not a robust intent classifier.
- Hybrid retrieval may return semantically close but irrelevant chunks; retrieval metrics and source checks are needed.
- Empty/garbled PDF extraction is not OCRed; scan-based PDFs need a different ingest pathway.
- Recommendations currently have **no scores** because validated domain candidate data is missing.
- Each agent calls Ollama sequentially to suit lower-powered laptops.
- The developer should test representative source PDFs and add proper error handling and model benchmarks before the hackathon demo.

## Clarification / unsupported route

The Manager does **not** default to Technology when no domain matches. It returns `selected_agents: []`, `needs_clarification: true`, `missing_information: [...]`, and `status: "needs_clarification"`. The LangGraph flow terminates via a dedicated `clarification` node: it does not call retrieval, specialists, or the recommender. The UI displays the clarification message. Keyword-based routing remains a baseline, so a question that happens to contain a trigger word may still be misrouted; robust intent classification is future work.
