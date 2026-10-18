"""Index local PDF/TXT files into both Chroma and SQLite FTS5, sharing stable chunk IDs."""
import hashlib, sqlite3, os
from pathlib import Path
import fitz
from sentence_transformers import SentenceTransformer
import chromadb
DOMAINS = ('technology','clinical','sec','csr')
def split_text(text: str, size: int=1000, overlap: int=150):
    clean=' '.join(text.split())
    return [clean[i:i+size] for i in range(0,len(clean),size-overlap) if clean[i:i+size].strip()]
def ingest(data_dir='data', index_dir='indexes'):
    root=Path(index_dir);root.mkdir(exist_ok=True,parents=True)
    sql=sqlite3.connect(root/'documents.sqlite')
    sql.execute('CREATE TABLE IF NOT EXISTS chunks (id TEXT UNIQUE, domain TEXT, source TEXT, page INTEGER, text TEXT)')
    sql.execute('CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content="chunks", content_rowid="rowid")')
    sql.execute('DELETE FROM chunks')
    sql.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
    client=chromadb.PersistentClient(path=str(root/'chroma'))
    embedder=SentenceTransformer(os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'))
    total=0
    for domain in DOMAINS:
        try: client.delete_collection(domain)
        except (ValueError, chromadb.errors.NotFoundError): pass
        collection=client.create_collection(domain)
        records=[]
        for path in (Path(data_dir)/domain).rglob('*'):
            if not path.is_file() or path.suffix.lower() not in ('.pdf','.txt'):continue
            if path.suffix.lower()=='.pdf':
                doc=fitz.open(path)
                pages=[(i+1,p.get_text()) for i,p in enumerate(doc)]
                doc.close()
            else:pages=[(1,path.read_text(encoding='utf-8',errors='replace'))]
            for page_num,txt in pages:
                for idx, chunk in enumerate(split_text(txt)):
                    identity=f'{domain}|{path.as_posix()}|{page_num}|{idx}'
                    id=hashlib.sha256(identity.encode()).hexdigest()[:24]
                    sql.execute('INSERT INTO chunks (id,domain,source,page,text) VALUES (?,?,?,?,?)', (id,domain,path.name,page_num,chunk))
                    records.append((id,chunk))
        if records:
            for start in range(0,len(records),64):
                batch=records[start:start+64]
                embeddings=embedder.encode([r[1] for r in batch],normalize_embeddings=True).tolist()
                collection.add(ids=[r[0] for r in batch],documents=[r[1] for r in batch],embeddings=embeddings)
            total += len(records)
            print(f'{domain}: {len(records)} chunks')
    sql.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    sql.commit();sql.close();print(f'Indexed {total} chunks total')
if __name__=='__main__':ingest()
