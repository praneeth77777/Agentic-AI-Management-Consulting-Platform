from __future__ import annotations
import argparse, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
import fitz
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.config import get_settings
from app.models.contracts import Domain
from app.retrieval.fts import connect, upsert_chunk

def chunks(text: str, size=1800, overlap=250):
    text = re.sub(r"\s+", " ", text).strip()
    if not text: return
    i = 0
    while i < len(text):
        yield text[i:i+size]
        i += max(1, size-overlap)

def metadata_for(path: Path, domain: Domain, page: int | None, idx: int, text: str):
    org = "Cisco" if "cisco" in str(path).lower() else "Alphabet" if "alphabet" in str(path).lower() else "Agilent" if "agilent" in str(path).lower() else None
    title = path.stem
    raw = f"{domain.value}|{path}|{page}|{idx}|{text}".encode()
    eid = hashlib.sha256(raw).hexdigest()[:20]
    return {"evidence_id": eid, "source_title": title, "organization": org, "publication_date": "", "document_type": path.suffix.lstrip("."), "domain": domain.value, "company_or_product": org or "", "page_number": page or -1, "section": "", "source_path": str(path), "chunk_index": idx, "content_hash": hashlib.sha256(text.encode()).hexdigest(), "ingested_at": datetime.now(timezone.utc).isoformat()}

def ingest_file(path: Path, domain: Domain, vector, conn):
    docs=[]
    if path.suffix.lower()==".pdf":
        with fitz.open(path) as pdf:
            for pno, page in enumerate(pdf, start=1):
                for idx, text in enumerate(chunks(page.get_text("text")) or []): docs.append((text, metadata_for(path, domain, pno, idx, text)))
    elif path.suffix.lower() in {".txt", ".md"}:
        for idx, text in enumerate(chunks(path.read_text(errors="ignore")) or []): docs.append((text, metadata_for(path, domain, None, idx, text)))
    for text, md in docs:
        vector.add_texts([text], metadatas=[md], ids=[md["evidence_id"]])
        row = dict(md); row["content"] = text; row["page_number"] = None if md["page_number"] == -1 else md["page_number"]
        upsert_chunk(conn, row)
    return len(docs)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--domain", required=True, choices=[d.value for d in Domain]); p.add_argument("--path", required=True); a=p.parse_args()
    domain=Domain(a.domain); s=get_settings(); emb=OllamaEmbeddings(base_url=s.ollama_base_url, model=s.ollama_embed_model)
    vector=Chroma(collection_name=f"domain_{domain.value}", embedding_function=emb, persist_directory=s.chroma_dir)
    conn=connect(s.fts_db); total=0
    root=Path(a.path); files=[root] if root.is_file() else [p for p in root.rglob("*") if p.suffix.lower() in {".pdf",".txt",".md"}]
    for f in files:
        n=ingest_file(f, domain, vector, conn); total += n; print(f"{f}: {n} chunks")
    conn.close(); print(f"TOTAL {total} chunks ingested for {domain.value}")
if __name__=="__main__": main()
