"""SkillSmith AI Package."""

from app.ai.exceptions import (
    AIError,
    AIConnectionError,
    AIModelError,
    AIAuthError,
    AITimeoutError,
)
from app.ai.provider import generate
from app.ai.ollama_client import (
    OllamaError,
    OllamaConnectionError,
    OllamaModelError,
)
from app.ai.vercel_client import (
    VercelAIError,
    VercelAIAuthError,
    VercelAIConnectionError,
    VercelAIModelError,
    VercelAITimeoutError,
)

__all__ = [
    "generate",
    "AIError",
    "AIConnectionError",
    "AIModelError",
    "AIAuthError",
    "AITimeoutError",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaModelError",
    "VercelAIError",
    "VercelAIAuthError",
    "VercelAIConnectionError",
    "VercelAIModelError",
    "VercelAITimeoutError",
]
