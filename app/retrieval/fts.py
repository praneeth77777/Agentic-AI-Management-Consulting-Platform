from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
  evidence_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  source_title TEXT NOT NULL,
  organization TEXT,
  document_type TEXT,
  source_path TEXT NOT NULL,
  page_number INTEGER,
  section TEXT,
  content TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  evidence_id UNINDEXED, domain UNINDEXED, source_title, content, tokenize='porter unicode61'
);
"""

def connect(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def upsert_chunk(conn, row: dict):
    conn.execute("DELETE FROM chunks_fts WHERE evidence_id=?", (row["evidence_id"],))
    conn.execute("INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", (
        row["evidence_id"], row["domain"], row["source_title"], row.get("organization"), row.get("document_type"),
        row["source_path"], row.get("page_number"), row.get("section"), row["content"]
    ))
    conn.execute("INSERT INTO chunks_fts(evidence_id,domain,source_title,content) VALUES (?,?,?,?)", (
        row["evidence_id"], row["domain"], row["source_title"], row["content"]
    ))
    conn.commit()
