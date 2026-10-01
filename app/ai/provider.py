"""
SkillSmith — AI Provider Abstraction

Unified interface across AI inference backends (local Ollama or Vercel AI Gateway).
Allows services (generator, repair, runner) to remain provider-agnostic.
"""

from app.core import config
from app.ai.exceptions import (
    AIError,
    AIConnectionError,
    AIModelError,
    AIAuthError,
    AITimeoutError,
)
from app.ai import ollama_client, vercel_client


async def generate(
    prompt: str,
    model: str | None = None,
    timeout: float = 120.0,
    *,
    schema: dict | None = None,
) -> str:
    """
    Dispatch generation request to the configured AI provider.

    Provider selection is controlled by config.AI_PROVIDER:
      - 'ollama': Local Ollama HTTP API (localhost:11434)
      - 'vercel': Hosted Vercel AI Gateway OpenAI-compatible API
    """
    provider = config.AI_PROVIDER.lower().strip()

    if provider == "ollama":
        return await ollama_client.generate(
            prompt=prompt,
            model=model,
            timeout=timeout,
            schema=schema,
        )
    elif provider == "vercel":
        return await vercel_client.generate(
            prompt=prompt,
            model=model,
            timeout=timeout,
            schema=schema,
        )
    else:
        raise AIError(
            f"Unsupported AI_PROVIDER '{config.AI_PROVIDER}'. "
            "Valid options are 'ollama' or 'vercel'."
        )
