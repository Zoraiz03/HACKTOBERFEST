# SkillSmith

**Turn any workflow into an AI Agent Skill.**

> 🏆 Hacktoberfest 2026 — COMSATS University Islamabad, Abbottabad Campus

---

## Overview

SkillSmith is an open-source AI-powered tool that transforms natural language workflow descriptions into reusable **Agent Skills** following the [Agent Skills Open Standard](https://github.com/agent-skills).

Describe what you want an AI agent to do, and SkillSmith generates a complete, validated, ready-to-use skill package.

## Current Development Status

> ⚠️ **This project is currently in the initial setup stage.**
>
> The project structure, environment configuration, and Ollama AI connection have been established.
>
> Skill generation, validation, and export are **not yet implemented**.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, FastAPI, Uvicorn |
| Frontend | HTML, Vanilla JavaScript, CSS |
| AI | Ollama (local), qwen2.5:3b |
| HTTP Client | httpx |
| Config | python-dotenv |

## Local Setup

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running
- qwen2.5:3b model pulled

### Installation

```bash
# Clone the repository
git clone https://github.com/Zoraiz03/HACKTOBERFEST.git
cd HACKTOBERFEST

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

## Ollama Setup

```bash
# Install Ollama (macOS)
brew install ollama

# Start the server
brew services start ollama

# Pull the model
ollama pull qwen2.5:3b
```

## Running the Hello-World Test

Verify that the Python → Ollama → AI model pipeline works:

```bash
python scripts/ollama_hello.py
```

Expected output:

```
============================================================
SkillSmith — Ollama Hello-World Test
============================================================
  Ollama URL : http://localhost:11434
  Model      : qwen2.5:3b
============================================================

Prompt: Reply with exactly: SkillSmith AI connection successful

Waiting for model response...

Response: SkillSmith AI connection successful

✅  Ollama connection verified successfully!
```

## Running the FastAPI Server

```bash
python run.py
```

The server starts at [http://localhost:8000](http://localhost:8000).

Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `MODEL_NAME` | Ollama model to use | `qwen2.5:3b` |

## Project Structure

```
skillsmith/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   └── config.py        # Centralized configuration
│   ├── ai/
│   │   └── ollama_client.py # Ollama HTTP client
│   ├── services/            # Business logic (coming soon)
│   ├── models/              # Data models (coming soon)
│   ├── templates/           # HTML templates
│   └── static/              # CSS & JS assets
├── scripts/
│   └── ollama_hello.py      # AI connection test
├── tests/                   # Test suite
├── generated_skills/        # Output directory for generated skills
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md
```

## AI Model Information

| Model | Provider | Parameters | License |
|-------|----------|-----------|---------|
| [qwen2.5:3b](https://ollama.com/library/qwen2.5:3b) | Alibaba / Qwen Team | 3B | [Apache 2.0](https://huggingface.co/Qwen/Qwen2.5-3B/blob/main/LICENSE) |

The model runs **locally** via Ollama. No data is sent to external APIs.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [Ollama](https://ollama.com/) — Local AI model serving
- [Qwen2.5](https://github.com/QwenLM/Qwen2.5) — Open-weight language model by Alibaba
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
