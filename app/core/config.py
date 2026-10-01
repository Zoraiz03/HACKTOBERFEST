"""
SkillSmith — Centralized Configuration

All environment variables are loaded here.
Other modules import settings from this file instead of reading env vars directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# AI Provider Configuration
# ---------------------------------------------------------------------------
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama").lower().strip()

# Ollama (Local)
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen2.5:3b")

# Vercel AI Gateway (Production)
VERCEL_AI_GATEWAY_API_KEY: str = os.getenv("VERCEL_AI_GATEWAY_API_KEY", "")
VERCEL_AI_GATEWAY_BASE_URL: str = os.getenv(
    "VERCEL_AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1"
)
VERCEL_AI_MODEL: str = os.getenv("VERCEL_AI_MODEL", "alibaba/qwen-3-32b")

# ---------------------------------------------------------------------------
# Application Configuration
# ---------------------------------------------------------------------------
APP_NAME: str = "SkillSmith"
APP_VERSION: str = "0.1.0"
APP_DESCRIPTION: str = "Turn any workflow into an AI Agent Skill."
