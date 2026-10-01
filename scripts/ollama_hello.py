"""
SkillSmith — Ollama Hello-World Test

Proves that the Python → Ollama → qwen2.5:14b pipeline works.

Usage:
    python -m scripts.ollama_hello
    # or
    python scripts/ollama_hello.py
"""

import asyncio
import sys
import os

# Ensure project root is on the path when run as a standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.ollama_client import generate, OllamaConnectionError, OllamaModelError, OllamaError
from app.core.config import MODEL_NAME, OLLAMA_BASE_URL


async def main():
    print("=" * 60)
    print("SkillSmith — Ollama Hello-World Test")
    print("=" * 60)
    print(f"  Ollama URL : {OLLAMA_BASE_URL}")
    print(f"  Model      : {MODEL_NAME}")
    print("=" * 60)
    print()

    prompt = "Reply with exactly: SkillSmith AI connection successful"

    print(f"Prompt: {prompt}")
    print()
    print("Waiting for model response...")
    print()

    try:
        response = await generate(prompt)
        print(f"Response: {response}")
        print()
        print("✅  Ollama connection verified successfully!")
    except OllamaConnectionError as e:
        print(f"❌  Connection failed: {e}")
        sys.exit(1)
    except OllamaModelError as e:
        print(f"❌  Model error: {e}")
        sys.exit(1)
    except OllamaError as e:
        print(f"❌  Ollama error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
