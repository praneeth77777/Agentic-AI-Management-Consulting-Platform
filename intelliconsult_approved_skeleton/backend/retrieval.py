"""Shared retriever. MOCK is default; real Chroma+SQLite FTS5 when configured."""
import os, sqlite3
from pathlib import Path
from .contracts import Evidence, Domain

MOCK = {
 'technology': ('Technology sample (synthetic)', 'Check device model, logs, power and hardware compatibility before replacement.'),
 'clinical': ('Clinical sample (synthetic)', 'Check laboratory sample throughput and instrument specifications before procurement.'),
 'sec': ('SEC sample (synthetic)', 'Review company filings for disclosed operational and supplier-related risks.'),
 'csr': ('CSR sample (synthetic)', 'Compare interventions using impact, feasibility and resource requirements.'),
}

def mock_retrieve(question: str, domain: Domain) -> list[Evidence]:
    source, passage = MOCK[domain]
    return [Evidence(id=f'mock-{domain}-1', domain=domain, source=source, page=1,
                     text=passage, retrieval='mock')]

def hybrid_retrieve(question: str, domain: Domain, limit: int = 4) -> list[Evidence]:
    if os.getenv('RETRIEVAL_MODE', 'mock') != 'hybrid':
        return mock_retrieve(question, domain)
    import chromadb
    from sentence_transformers import SentenceTransformer
    root = Path(os.getenv('INDEX_DIR', 'indexes'))
    db_path = root / 'documents.sqlite'
    if not db_path.exists():
        raise RuntimeError('No local indexes. Run: python -m backend.ingest')
    model = SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
    client = chromadb.PersistentClient(path=str(root / 'chroma'))
    collection = client.get_collection(name=domain)
    embedding = model.encode([question], normalize_embeddings=True)[0].tolist()
    vector_results = collection.query(query_embeddings=[embedding], n_results=min(limit*2,max(1,collection.count())))
    semantic_ids = vector_results['ids'][0]
    connection = sqlite3.connect(db_path)
    try:
        # FTS5 match query is quoted to avoid syntax errors from user-supplied punctuation.
        tokens = [w for w in __import__('re').findall(r'[A-Za-z0-9]+', question) if len(w)>2]
        search = ' OR '.join('"'+w.replace('"','')+'"' for w in tokens[:12])
        keyword_ids = []
        if search:
            try:
                keyword_ids = [r[0] for r in connection.execute(
                    'SELECT c.id FROM chunks_fts f JOIN chunks c ON c.rowid=f.rowid '
                    'WHERE chunks_fts MATCH ? AND c.domain=? ORDER BY bm25(chunks_fts) LIMIT ?',
                    (search, domain, limit*2)).fetchall()]
            except sqlite3.OperationalError:
                keyword_ids = []
        # Reciprocal rank fusion (RRF): does not combine incomparable raw scores.
        scores: dict[str,float] = {}
        for results in (semantic_ids, keyword_ids):
            for rank, doc_id in enumerate(results, start=1):
                scores[doc_id] = scores.get(doc_id,0.0) + 1.0/(60+rank)
        result = []
        for doc_id in sorted(scores,key=scores.get,reverse=True)[:limit]:
            row = connection.execute('SELECT domain, source, page, text FROM chunks WHERE id=? AND domain=?', (doc_id, domain)).fetchone()
            if row:
                result.append(Evidence(id=doc_id, domain=row[0],source=row[1],page=row[2],text=row[3],retrieval='hybrid'))
        return result
    finally:
        connection.close()
