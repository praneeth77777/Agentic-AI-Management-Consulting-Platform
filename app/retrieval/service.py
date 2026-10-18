from __future__ import annotations

import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.config import get_settings
from app.models.contracts import Domain, Evidence
from app.retrieval.fts import connect


SEC_POSITIVE_TERMS = {
    "item 1a": 0.012,
    "risk factors": 0.012,
    "supply chain impacts and risks": 0.015,
    "cybersecurity": 0.010,
    "cybersecurity risk": 0.012,
    "third-party": 0.006,
    "supplier": 0.006,
    "suppliers": 0.006,
    "customer": 0.004,
    "customers": 0.004,
    "product defect": 0.008,
    "product defects": 0.008,
    "product recall": 0.008,
    "litigation": 0.006,
    "regulatory": 0.006,
    "operational risk": 0.010,
    "financial condition": 0.006,
    "materially adversely": 0.006,
}

SEC_NEGATIVE_TERMS = {
    "insider trading": 0.060,
    "trading window": 0.060,
    "material non-public information": 0.055,
    "material, non-public information": 0.055,
    "non-public information": 0.050,
    "transact in cisco securities": 0.050,
    "cisco legal department": 0.025,
    "stock splits": 0.020,
    "repurchase program for securities": 0.020,
}

def build_fts_query(query: str) -> str:
    """
    Convert a natural-language query into a safe SQLite FTS5 OR query.

    Removes punctuation such as hyphens that FTS5 may interpret as syntax.
    Quoting each token also prevents accidental column/filter expressions.
    """
    tokens = re.findall(r"[A-Za-z0-9]+", query.lower())

    # Remove tiny/noisy tokens while preserving useful terms such as 1a.
    tokens = [
        token
        for token in tokens
        if len(token) >= 2
    ]

    # Remove duplicates while preserving order.
    tokens = list(dict.fromkeys(tokens))

    return " OR ".join(
        f'"{token}"'
        for token in tokens
    )

class HybridRetriever:
    def __init__(self):
        s = get_settings()

        Path(s.chroma_dir).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.settings = s

        self.embeddings = OllamaEmbeddings(
            base_url=s.ollama_base_url,
            model=s.ollama_embed_model,
        )

    def _store(self, domain: Domain):
        return Chroma(
            collection_name=f"domain_{domain.value}",
            embedding_function=self.embeddings,
            persist_directory=self.settings.chroma_dir,
        )

    def _sec_rerank_bonus(
        self,
        evidence: Evidence,
        query: str,
    ) -> float:
        """
        Add a small deterministic reranking adjustment for SEC evidence.

        This does not replace vector/FTS retrieval. It only improves the final
        ordering of already-retrieved SEC candidates.
        """
        text = " ".join(
            [
                evidence.source_title or "",
                evidence.section or "",
                evidence.content or "",
            ]
        ).lower()

        bonus = 0.0

        for term, weight in SEC_POSITIVE_TERMS.items():
            if term in text:
                bonus += weight

        for term, weight in SEC_NEGATIVE_TERMS.items():
            if term in text:
                bonus -= weight

        query_lower = query.lower()

        # Keep company/entity matches high when the user explicitly names them.
        if "cisco" in query_lower:
            if (
                evidence.organization
                and evidence.organization.lower() == "cisco"
            ):
                bonus += 0.012

        if "alphabet" in query_lower or "google" in query_lower:
            if (
                evidence.organization
                and evidence.organization.lower() == "alphabet"
            ):
                bonus += 0.012

        if "agilent" in query_lower:
            if (
                evidence.organization
                and evidence.organization.lower() == "agilent"
            ):
                bonus += 0.012

        return bonus

    def search(
        self,
        query: str,
        domain: Domain,
        k: int = 5,
    ) -> list[Evidence]:
        candidates: dict[str, Evidence] = {}

        vector_rank: dict[str, int] = {}
        keyword_rank: dict[str, int] = {}

        # -----------------------------
        # Vector retrieval
        # -----------------------------
        try:
            docs = self._store(
                domain
            ).similarity_search_with_relevance_scores(
                query,
                k=max(k * 3, 15),
                filter={"domain": domain.value},
            )

            for rank, (doc, rel) in enumerate(
                docs,
                start=1,
            ):
                eid = doc.metadata["evidence_id"]

                vector_rank[eid] = rank

                candidates[eid] = Evidence(
                    evidence_id=eid,
                    domain=domain,
                    source_title=doc.metadata.get(
                        "source_title",
                        "Unknown",
                    ),
                    organization=doc.metadata.get(
                        "organization"
                    ),
                    document_type=doc.metadata.get(
                        "document_type"
                    ),
                    source_path=doc.metadata.get(
                        "source_path",
                        "",
                    ),
                    page_number=doc.metadata.get(
                        "page_number"
                    ),
                    section=doc.metadata.get(
                        "section"
                    ),
                    content=doc.page_content,
                    score=float(rel),
                )

        except Exception as exc:
            print(
                f"[retrieval] Vector search failed "
                f"for domain={domain.value}: {exc}"
            )

        # -----------------------------
        # SQLite FTS5 retrieval
        # -----------------------------
        conn = connect(
            self.settings.fts_db
        )

        try:
            fts_query = build_fts_query(query)

            rows = conn.execute(
                """
                SELECT
                    c.*,
                    bm25(chunks_fts) AS rank_score
                FROM chunks_fts
                JOIN chunks c USING(evidence_id)
                WHERE chunks_fts MATCH ?
                  AND c.domain=?
                ORDER BY rank_score
                LIMIT ?
                """,
                (
                    fts_query,
                    domain.value,
                    max(k * 3, 15),
                ),
            ).fetchall()

        except Exception as exc:
            print(
                f"[retrieval] Keyword search failed "
                f"for domain={domain.value}: {exc}"
            )
            rows = []

        finally:
            conn.close()

        for rank, row in enumerate(
            rows,
            start=1,
        ):
            eid = row["evidence_id"]

            keyword_rank[eid] = rank

            if eid not in candidates:
                candidates[eid] = Evidence(
                    evidence_id=eid,
                    domain=domain,
                    source_title=row["source_title"],
                    organization=row["organization"],
                    document_type=row["document_type"],
                    source_path=row["source_path"],
                    page_number=row["page_number"],
                    section=row["section"],
                    content=row["content"],
                    score=0.0,
                )

        # -----------------------------
        # Reciprocal rank fusion
        # -----------------------------
        scored: list[Evidence] = []

        for eid, evidence in candidates.items():
            rrf = 0.0

            if eid in vector_rank:
                rrf += 1 / (
                    60 + vector_rank[eid]
                )

            if eid in keyword_rank:
                rrf += 1 / (
                    60 + keyword_rank[eid]
                )

            final_score = rrf

            # SEC-aware deterministic reranking.
            if domain == Domain.sec:
                final_score += self._sec_rerank_bonus(
                    evidence,
                    query,
                )

            evidence.score = round(
                final_score,
                6,
            )

            scored.append(
                evidence
            )

        scored.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return scored[:k]