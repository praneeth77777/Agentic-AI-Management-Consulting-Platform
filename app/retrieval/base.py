"""Retrieval boundary used by agents.

This file Defines how agents request evidence.

Replace JsonlKeywordRetriever with the planned Chroma + SQLite FTS5 hybrid
implementation without changing graph or specialist contracts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from app.models import Domain, Evidence


class EvidenceRetriever(Protocol):
    def search(self, query: str, domain: Domain, limit: int = 5) -> list[Evidence]: ...


class NullRetriever:
    def search(self, query: str, domain: Domain, limit: int = 5) -> list[Evidence]:
        del query, domain, limit
        return []


class InMemoryRetriever:
    """Small deterministic retriever intended for tests and local experiments."""

    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = evidence

    def search(self, query: str, domain: Domain, limit: int = 5) -> list[Evidence]:
        del query
        return [item for item in self._evidence if item.domain == domain][:limit]


class JsonlKeywordRetriever:
    """Temporary zero-dependency retriever for validated evidence JSONL."""

    def __init__(self, path: Path) -> None:
        self._items = self._load(path)

    @staticmethod
    def _load(path: Path) -> list[Evidence]:
        if not path.is_file():
            raise FileNotFoundError(f"Evidence JSONL does not exist: {path}")
        items: list[Evidence] = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    items.append(Evidence.model_validate(json.loads(line)))
                except (json.JSONDecodeError, ValueError) as exc:
                    raise ValueError(f"Invalid evidence at {path}:{line_number}: {exc}") from exc
        return items

    def search(self, query: str, domain: Domain, limit: int = 5) -> list[Evidence]:
        query_terms = _terms(query)
        ranked: list[tuple[float, Evidence]] = []
        for item in self._items:
            if item.domain != domain:
                continue
            item_terms = _terms(f"{item.source_title} {item.section or ''} {item.content}")
            overlap = len(query_terms & item_terms)
            if overlap == 0:
                continue
            score = overlap / max(1, len(query_terms))
            ranked.append((score, item.model_copy(update={"score": min(1.0, score)})))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:limit]]


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9-]+", text.lower()) if len(term) >= 3}

