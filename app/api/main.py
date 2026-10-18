from __future__ import annotations
import time
from fastapi import FastAPI, HTTPException
from app.graph.workflow import graph, new_state
from app.models.contracts import QueryRequest, QueryResponse

app = FastAPI(title="Agentic AI Management Consulting Platform", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/consult", response_model=QueryResponse)
def consult(req: QueryRequest):
    start = time.perf_counter()
    try:
        state = graph.invoke(new_state(req.question))
        return QueryResponse(
            request_id=state["request_id"], route=state["route"], reports=state.get("reports", []),
            verification=state["verification"], recommendation=state["recommendation"],
            latency_ms=round((time.perf_counter()-start)*1000, 2)
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
