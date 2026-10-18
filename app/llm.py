"""Create the single shared Ollama chat-model client."""

from __future__ import annotations

from langchain_ollama import ChatOllama

from app.config import Settings


def create_ollama_model(settings: Settings) -> ChatOllama:
    """Return one client shared by the manager and every specialist."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        num_ctx=settings.ollama_num_ctx,
        client_kwargs={"timeout": settings.ollama_timeout_seconds},
    )

