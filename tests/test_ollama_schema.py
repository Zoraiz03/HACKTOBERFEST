"""Confirm schema reaches Ollama's HTTP API for structured decoding."""
import asyncio
import json

import httpx

from app.ai import ollama_client
from app.models import GeneratedSkillDraft


def test_schema_forwarded(monkeypatch):
    schema = GeneratedSkillDraft.model_json_schema()
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"response": "{}"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", lambda **kwargs: client)
    assert asyncio.run(ollama_client.generate("Test", schema=schema)) == "{}"
    assert requests[0]["format"] == schema
    assert requests[0]["stream"] is False
