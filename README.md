# SkillSmith

**Turn any workflow into an AI Agent Skill.**

> 🏆 Hacktoberfest 2026 — COMSATS University Islamabad, Abbottabad Campus

---

## Overview

SkillSmith is an open-source AI-powered tool that transforms natural language workflow descriptions into reusable **Agent Skills** following the [Agent Skills Open Standard](https://github.com/agent-skills).

Describe what you want an AI agent to do, and SkillSmith generates a complete, validated, ready-to-use skill package.

## Current Development Status

> **Core pipeline operational:**
>
> ✅ Local AI generation (Ollama + qwen2.5:3b)  
> ✅ Structured skill draft via AI  
> ✅ Deterministic SKILL.md assembly  
> ✅ Agent Skills Open Standard validation  
> ⬜ AI-powered repair loop  
> ⬜ Full UI  
> ⬜ ZIP export

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, FastAPI, Uvicorn |
| Frontend | HTML, Vanilla JavaScript, CSS |
| AI | Ollama (local), qwen2.5:3b |
| HTTP Client | httpx |
| YAML | PyYAML |
| Config | python-dotenv |
| Testing | pytest |

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

## Running Tests

```bash
pytest tests/ -v
```

## How AI Is Used

SkillSmith uses a **local open-weight AI model** as the core of its pipeline:

```
Workflow description (natural language)
        ↓
Local AI model (qwen2.5:3b via Ollama)
        ↓
Structured skill draft (JSON)
        ↓
Deterministic SKILL.md assembler (Python — no AI)
        ↓
Agent Skills spec validator (Python — no AI)
        ↓
Validated SKILL.md output
```

**Key design decision:** The AI generates structured data only. SKILL.md formatting and spec validation are handled deterministically in Python, ensuring reliable, spec-compliant output.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/generate` | Generate a structured skill draft from a workflow |
| `POST` | `/api/assemble` | Assemble SKILL.md and validate against Agent Skills spec |

### Validation

The validator checks skills against the Agent Skills Open Standard MVP rules:

- **Name:** 1–64 chars, lowercase `a-z`, digits `0-9`, hyphens only. No leading/trailing/consecutive hyphens.
- **Description:** 1–1024 chars, non-empty.
- **Instructions:** Non-empty body content.
- **Directory match:** Skill name must match parent directory name (when applicable).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `MODEL_NAME` | Ollama model to use | `qwen2.5:3b` |

## Project Structure

```
skillsmith/
├── app/
│   ├── main.py                # FastAPI application & endpoints
│   ├── core/
│   │   └── config.py          # Centralized configuration
│   ├── ai/
│   │   └── ollama_client.py   # Ollama HTTP client (httpx)
│   ├── services/
│   │   ├── generator.py       # AI skill generation + prompt
│   │   ├── assembler.py       # Deterministic SKILL.md builder
│   │   └── validator.py       # Agent Skills spec validator
│   ├── models/                # Pydantic data models
│   ├── templates/             # HTML templates
│   └── static/                # CSS & JS assets
├── scripts/
│   └── ollama_hello.py        # AI connection test
├── tests/
│   ├── test_validator.py      # 13 validation test cases
│   └── test_assembler.py      # 7 assembler output tests
├── generated_skills/          # Output directory
├── .env.example
├── requirements.txt
├── run.py
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
