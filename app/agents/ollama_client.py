from __future__ import annotations
import json
from typing import TypeVar, Type
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from app.config import get_settings

T = TypeVar("T", bound=BaseModel)

class OllamaJSONClient:
    def __init__(self):
        s = get_settings()
        self.model = ChatOllama(base_url=s.ollama_base_url, model=s.ollama_model, temperature=0)

    def invoke_structured(self, prompt: str, schema: Type[T]) -> T:
        schema_text = json.dumps(schema.model_json_schema(), indent=2)
        full = f"""{prompt}\n\nReturn ONLY valid JSON matching this JSON Schema:\n{schema_text}\nDo not add markdown or chain-of-thought."""
        msg = self.model.invoke(full)
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        text = text.strip().removeprefix("```json").removesuffix("```").strip()
        return schema.model_validate_json(text)
