"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_num_ctx: int = 8192
    ollama_timeout_seconds: float = 180.0
    max_concurrency: int = 1
    retrieval_top_k: int = 5
    evidence_jsonl: Path | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        evidence_path = os.getenv("EVIDENCE_JSONL")
        return cls(
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url),
            ollama_num_ctx=int(os.getenv("OLLAMA_NUM_CTX", str(cls.ollama_num_ctx))),
            ollama_timeout_seconds=float(
                os.getenv("OLLAMA_TIMEOUT_SECONDS", str(cls.ollama_timeout_seconds))
            ),
            max_concurrency=max(1, int(os.getenv("MAX_CONCURRENCY", "1"))),
            retrieval_top_k=max(1, int(os.getenv("RETRIEVAL_TOP_K", "5"))),
            evidence_jsonl=Path(evidence_path) if evidence_path else None,
        )

