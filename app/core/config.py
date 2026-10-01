"""
SkillSmith — Centralized Configuration

All environment variables are loaded here.
Other modules import settings from this file instead of reading env vars directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Ollama / AI Configuration
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen2.5:3b")

# ---------------------------------------------------------------------------
# Application Configuration
# ---------------------------------------------------------------------------
APP_NAME: str = "SkillSmith"
APP_VERSION: str = "0.1.0"
APP_DESCRIPTION: str = "Turn any workflow into an AI Agent Skill."
