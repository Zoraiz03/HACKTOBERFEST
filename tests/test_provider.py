"""Tests for AI provider abstraction and Vercel AI Gateway client."""

import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from app.ai import provider, vercel_client, ollama_client, AIError
from app.ai.vercel_client import (
    VercelAIAuthError,
    VercelAIConnectionError,
    VercelAIModelError,
    VercelAITimeoutError,
)
from app.core import config

_ORIG_ASYNC_CLIENT = httpx.AsyncClient


def test_provider_dispatch_ollama(monkeypatch):
    """Verify AI_PROVIDER=ollama dispatches to ollama_client.generate."""
    monkeypatch.setattr(config, "AI_PROVIDER", "ollama")
    mock_ollama = AsyncMock(return_value="ollama output")
    monkeypatch.setattr(ollama_client, "generate", mock_ollama)

    result = asyncio.run(provider.generate("test prompt", model="custom-model"))
    assert result == "ollama output"
    mock_ollama.assert_awaited_once_with(
        prompt="test prompt",
        model="custom-model",
        timeout=120.0,
        schema=None,
    )


def test_provider_dispatch_vercel(monkeypatch):
    """Verify AI_PROVIDER=vercel dispatches to vercel_client.generate."""
    monkeypatch.setattr(config, "AI_PROVIDER", "vercel")
    mock_vercel = AsyncMock(return_value="vercel output")
    monkeypatch.setattr(vercel_client, "generate", mock_vercel)

    result = asyncio.run(provider.generate("test prompt", schema={"type": "object"}))
    assert result == "vercel output"
    mock_vercel.assert_awaited_once_with(
        prompt="test prompt",
        model=None,
        timeout=120.0,
        schema={"type": "object"},
    )


def test_provider_dispatch_unknown(monkeypatch):
    """Verify unknown provider raises AIError."""
    monkeypatch.setattr(config, "AI_PROVIDER", "unsupported_backend")
    with pytest.raises(AIError, match="Unsupported AI_PROVIDER"):
        asyncio.run(provider.generate("test prompt"))


def test_vercel_missing_key(monkeypatch):
    """Verify Vercel client fails immediately if API key is not configured."""
    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_API_KEY", "")
    with pytest.raises(VercelAIAuthError, match="VERCEL_AI_GATEWAY_API_KEY is not set"):
        asyncio.run(vercel_client.generate("test prompt"))


def test_vercel_client_success(monkeypatch):
    """Verify successful request to Vercel AI Gateway OpenAI-compatible endpoint."""
    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_API_KEY", "secret-test-key")
    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")
    monkeypatch.setattr(config, "VERCEL_AI_MODEL", "alibaba/qwen-3-32b")

    captured_requests = []

    def mock_handler(request: httpx.Request):
        captured_requests.append({
            "url": str(request.url),
            "headers": dict(request.headers),
            "body": json.loads(request.content.decode("utf-8")),
        })
        response_body = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"name": "test-skill"}',
                    }
                }
            ]
        }
        return httpx.Response(200, json=response_body)

    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_handler)),
    )

    result = asyncio.run(
        vercel_client.generate("Prompt here", schema={"type": "object"})
    )
    assert result == '{"name": "test-skill"}'
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req["url"] == "https://ai-gateway.vercel.sh/v1/chat/completions"
    assert req["headers"]["authorization"] == "Bearer secret-test-key"
    assert req["body"]["model"] == "alibaba/qwen-3-32b"
    assert req["body"]["response_format"] == {"type": "json_object"}
    assert req["body"]["messages"][0]["content"] == "Prompt here"


def test_vercel_client_cleans_markdown_fences(monkeypatch):
    """Verify markdown code fences are stripped from response if present."""
    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_API_KEY", "secret-test-key")

    def mock_handler(request):
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "```json\n{\"ok\": true}\n```"}}]
        })

    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_handler)),
    )

    result = asyncio.run(vercel_client.generate("Prompt"))
    assert result == '{"ok": true}'


def test_vercel_client_errors(monkeypatch):
    """Verify network, timeout, and status error translations."""
    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_API_KEY", "secret-key")

    # 401 Auth Error
    def mock_401(req):
        return httpx.Response(401, text="Unauthorized")
    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_401)),
    )
    with pytest.raises(VercelAIAuthError):
        asyncio.run(vercel_client.generate("Prompt"))

    # 404 Model Error
    def mock_404(req):
        return httpx.Response(404, text="Model not found")
    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_404)),
    )
    with pytest.raises(VercelAIModelError):
        asyncio.run(vercel_client.generate("Prompt"))

    # Connect Error
    def mock_connect(req):
        raise httpx.ConnectError("Connection refused")
    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_connect)),
    )
    with pytest.raises(VercelAIConnectionError):
        asyncio.run(vercel_client.generate("Prompt"))

    # Timeout Error
    def mock_timeout(req):
        raise httpx.TimeoutException("Timed out")
    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_timeout)),
    )
    with pytest.raises(VercelAITimeoutError):
        asyncio.run(vercel_client.generate("Prompt"))


@pytest.mark.parametrize("raw_model_output,expected_name", [
    (
        '{"name": "clean-skill", "description": "Desc", "instructions": "1. Step", "example": {"input": "in", "output": "out"}}',
        "clean-skill",
    ),
    (
        '```json\n{"name": "fenced-skill", "description": "Desc", "instructions": "1. Step", "example": {"input": "in", "output": "out"}}\n```',
        "fenced-skill",
    ),
    (
        '   \n\t{"name": "spaced-skill", "description": "Desc", "instructions": "1. Step", "example": {"input": "in", "output": "out"}}\n  ',
        "spaced-skill",
    ),
    (
        '<think>Analyzing request...</think>\n```json\n{"name": "reasoning-skill", "description": "Desc", "instructions": "1. Step", "example": {"input": "in", "output": "out"}}\n```',
        "reasoning-skill",
    ),
    (
        'Here is the generated skill:\n```json\n{"name": "prose-skill", "description": "Desc", "instructions": "1. Step", "example": {"input": "in", "output": "out"}}\n```\nHope this helps!',
        "prose-skill",
    ),
])
def test_vercel_client_realistic_payload_extractions(monkeypatch, raw_model_output, expected_name):
    """Test realistic hosted Qwen responses are cleanly extracted and parsed."""
    from app.services.generator import parse_skill_draft

    monkeypatch.setattr(config, "VERCEL_AI_GATEWAY_API_KEY", "secret-test-key")

    def mock_handler(request):
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": raw_model_output}}]
        })

    monkeypatch.setattr(
        vercel_client.httpx,
        "AsyncClient",
        lambda **kwargs: _ORIG_ASYNC_CLIENT(transport=httpx.MockTransport(mock_handler)),
    )

    extracted_text = asyncio.run(vercel_client.generate("Prompt", schema={"type": "object"}))
    draft = parse_skill_draft(extracted_text)
    assert draft.name == expected_name
    assert draft.description == "Desc"
    assert draft.instructions == "1. Step"
    assert draft.example.input == "in"


def test_parse_skill_draft_field_normalizations():
    """Verify list instructions and array examples are normalized cleanly."""
    from app.services.generator import parse_skill_draft

    # List of instructions & list of examples
    payload = json.dumps({
        "name": "normalized-skill",
        "description": "A normalized skill.",
        "instructions": ["1. First step", "2. Second step"],
        "example": [{"input": "sample in", "output": "sample out"}],
    })
    draft = parse_skill_draft(payload)
    assert draft.name == "normalized-skill"
    assert draft.instructions == "1. First step\n2. Second step"
    assert draft.example.input == "sample in"


def test_parse_skill_draft_malformed_and_schema_violations():
    """Verify malformed JSON and schema violations raise clear errors."""
    from pydantic import ValidationError
    from app.services.generator import parse_skill_draft

    # 1. Malformed JSON
    with pytest.raises(ValidationError):
        parse_skill_draft("Not JSON at all")

    # 2. Valid JSON violating schema (missing required fields)
    with pytest.raises(ValidationError):
        parse_skill_draft('{"name": "missing-fields-only"}')


def test_parse_skill_draft_structured_example_output():
    """Verify example.output provided as a dictionary/object or list is preserved and converted to string."""
    from app.services.generator import parse_skill_draft

    payload = json.dumps({
        "name": "meeting-extractor",
        "description": "Extract decisions and action items from meeting notes.",
        "instructions": "1. Read notes.\n2. Extract items.",
        "example": {
            "input": {"raw_notes": "Alice ships Friday"},
            "output": {
                "decisions": ["Ship on Friday"],
                "action_items": [{"task": "Ship", "owner": "Alice", "deadline": "Friday"}]
            }
        }
    })
    draft = parse_skill_draft(payload)
    assert draft.name == "meeting-extractor"
    assert isinstance(draft.example.output, str)
    assert isinstance(draft.example.input, str)
    assert "Ship on Friday" in draft.example.output
    assert "Alice ships Friday" in draft.example.input


