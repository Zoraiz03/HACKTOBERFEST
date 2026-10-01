"""
SkillSmith — Ollama Client

Reusable async client for communicating with a local Ollama server
via its HTTP API. Uses httpx instead of a heavyweight SDK.
"""

import httpx
from app.core.config import OLLAMA_BASE_URL, MODEL_NAME
from app.ai.exceptions import AIError, AIConnectionError, AIModelError


class OllamaError(AIError):
    """Base exception for Ollama-related errors."""


class OllamaConnectionError(OllamaError, AIConnectionError):
    """Raised when the Ollama server is unreachable."""


class OllamaModelError(OllamaError, AIModelError):
    """Raised when the requested model is not available."""


async def generate(
    prompt: str, model: str | None = None, timeout: float = 120.0,
    *, schema: dict | None = None,
) -> str:
    """
    Send a prompt to Ollama and return the generated text.

    Args:
        prompt:  The text prompt to send.
        model:   Model name override. Defaults to MODEL_NAME from config.
        timeout: Request timeout in seconds (default 120s).

    Returns:
        The generated text string from the model.

    Raises:
        OllamaConnectionError: If Ollama server is unreachable.
        OllamaModelError:      If the requested model is not available.
        OllamaError:           For any other Ollama-related error.
    """
    model = model or MODEL_NAME
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if schema is not None:
        payload["format"] = schema

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
    except httpx.ConnectError:
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            "Is the Ollama server running? Start it with: ollama serve"
        )
    except httpx.TimeoutException:
        raise OllamaError(
            f"Ollama request timed out after {timeout}s. "
            "The model may be loading or the prompt may be too complex."
        )

    if response.status_code == 404:
        raise OllamaModelError(
            f"Model '{model}' not found. "
            f"Pull it with: ollama pull {model}"
        )

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned status {response.status_code}: {response.text}"
        )

    data = response.json()
    return data.get("response", "")
