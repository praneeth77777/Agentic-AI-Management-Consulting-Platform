from __future__ import annotations
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.config import get_settings
from app.models.contracts import Domain, Evidence
from app.retrieval.fts import connect

class HybridRetriever:
    def __init__(self):
        s = get_settings()
        Path(s.chroma_dir).mkdir(parents=True, exist_ok=True)
        self.settings = s
        self.embeddings = OllamaEmbeddings(base_url=s.ollama_base_url, model=s.ollama_embed_model)

    def _store(self, domain: Domain):
        return Chroma(collection_name=f"domain_{domain.value}", embedding_function=self.embeddings, persist_directory=self.settings.chroma_dir)

    def search(self, query: str, domain: Domain, k: int = 5) -> list[Evidence]:
        candidates: dict[str, Evidence] = {}
        vector_rank: dict[str, int] = {}
        keyword_rank: dict[str, int] = {}
        try:
            docs = self._store(domain).similarity_search_with_relevance_scores(query, k=max(k, 8), filter={"domain": domain.value})
            for rank, (doc, rel) in enumerate(docs, start=1):
                eid = doc.metadata["evidence_id"]
                vector_rank[eid] = rank
                candidates[eid] = Evidence(
                    evidence_id=eid, domain=domain, source_title=doc.metadata.get("source_title", "Unknown"),
                    organization=doc.metadata.get("organization"), document_type=doc.metadata.get("document_type"),
                    source_path=doc.metadata.get("source_path", ""), page_number=doc.metadata.get("page_number"),
                    section=doc.metadata.get("section"), content=doc.page_content, score=float(rel)
                )
        except Exception:
            pass
        conn = connect(self.settings.fts_db)
        try:
            rows = conn.execute("""
                SELECT c.*, bm25(chunks_fts) AS rank_score
                FROM chunks_fts JOIN chunks c USING(evidence_id)
                WHERE chunks_fts MATCH ? AND c.domain=? ORDER BY rank_score LIMIT ?
            """, (query, domain.value, max(k, 8))).fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()
        for rank, row in enumerate(rows, start=1):
            eid = row["evidence_id"]
            keyword_rank[eid] = rank
            if eid not in candidates:
                candidates[eid] = Evidence(
                    evidence_id=eid, domain=domain, source_title=row["source_title"], organization=row["organization"],
                    document_type=row["document_type"], source_path=row["source_path"], page_number=row["page_number"],
                    section=row["section"], content=row["content"], score=0.0
                )
        # reciprocal rank fusion
        scored = []
        for eid, ev in candidates.items():
            rrf = (1/(60+vector_rank[eid]) if eid in vector_rank else 0) + (1/(60+keyword_rank[eid]) if eid in keyword_rank else 0)
            ev.score = round(rrf, 6)
            scored.append(ev)
        return sorted(scored, key=lambda x: x.score, reverse=True)[:k]
