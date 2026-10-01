"""
SkillSmith — Vercel AI Gateway Client

Async client for communicating with Vercel AI Gateway via its
OpenAI-compatible HTTP API (/chat/completions). Uses httpx.
"""

import httpx
from app.core import config
from app.ai.exceptions import (
    AIError,
    AIAuthError,
    AIConnectionError,
    AIModelError,
    AITimeoutError,
)


class VercelAIError(AIError):
    """Base exception for Vercel AI Gateway errors."""


class VercelAIAuthError(VercelAIError, AIAuthError):
    """Raised when authentication fails (missing or invalid API key)."""


class VercelAIConnectionError(VercelAIError, AIConnectionError):
    """Raised when the Vercel AI Gateway is unreachable."""


class VercelAIModelError(VercelAIError, AIModelError):
    """Raised when the requested model is not found or unsupported."""


class VercelAITimeoutError(VercelAIError, AITimeoutError):
    """Raised when a request to Vercel AI Gateway times out."""


def _clean_markdown_fences(content: str) -> str:
    """Strip optional markdown code fences if returned by the model."""
    text = content.strip()
    if text.startswith("```json"):
        text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
    elif text.startswith("```"):
        text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


async def generate(
    prompt: str,
    model: str | None = None,
    timeout: float = 120.0,
    *,
    schema: dict | None = None,
) -> str:
    """
    Send a prompt to Vercel AI Gateway and return the generated text.

    Args:
        prompt:  The text prompt to send.
        model:   Model name override. Defaults to VERCEL_AI_MODEL from config.
        timeout: Request timeout in seconds (default 120s).
        schema:  Optional JSON schema dictionary for structured output.

    Returns:
        The generated text string from the model.
    """
    api_key = config.VERCEL_AI_GATEWAY_API_KEY.strip()
    if not api_key:
        raise VercelAIAuthError(
            "VERCEL_AI_GATEWAY_API_KEY is not set. "
            "Please configure VERCEL_AI_GATEWAY_API_KEY in your environment variables."
        )

    model = model or config.VERCEL_AI_MODEL
    base_url = config.VERCEL_AI_GATEWAY_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
    }

    if schema is not None:
        payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.ConnectError as exc:
        raise VercelAIConnectionError(
            f"Cannot connect to Vercel AI Gateway at {base_url}. Network error: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise VercelAITimeoutError(
            f"Vercel AI Gateway request timed out after {timeout}s."
        ) from exc

    if response.status_code in (401, 403):
        raise VercelAIAuthError(
            f"Vercel AI Gateway authentication failed ({response.status_code}): {response.text}"
        )

    if response.status_code == 404:
        raise VercelAIModelError(
            f"Model '{model}' not found on Vercel AI Gateway ({response.status_code}): {response.text}"
        )

    if response.status_code != 200:
        raise VercelAIError(
            f"Vercel AI Gateway returned status {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise VercelAIError(
            f"Malformed response from Vercel AI Gateway: {response.text}"
        ) from exc

    return _clean_markdown_fences(raw_text or "")
