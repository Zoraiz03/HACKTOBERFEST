"""SkillSmith — AI Exceptions."""


class AIError(Exception):
    """Base exception for all AI provider errors."""


class AIConnectionError(AIError):
    """Raised when the AI provider server is unreachable."""


class AIModelError(AIError):
    """Raised when the requested model is not found or unsupported."""


class AIAuthError(AIError):
    """Raised when authentication fails (missing or invalid API key)."""


class AITimeoutError(AIError):
    """Raised when an AI request times out."""
