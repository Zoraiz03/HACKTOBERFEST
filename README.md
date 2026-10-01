# SkillSmith

**Turn any workflow into a reusable AI Agent Skill.**

## Problem

Creating Agent Skills manually requires converting a workflow into structured instructions, following the Agent Skills format, validating the result, and testing whether it actually works. AI can generate instructions, but its output is not always specification-compliant. SkillSmith combines local AI generation with deterministic validation and a built-in test interface.

## Solution

```text
Describe Workflow
        ↓
Qwen2.5 3B (local via Ollama)
        ↓
Structured Skill Draft
        ↓
Deterministic Python Validator
        ↓
Invalid? → AI Repair using exact validation errors
        ↓              ↓
        ← Deterministic Re-validation (maximum 2 attempts)
        ↓ valid
SKILL.md Assembly
        ↓
Test Skill
        ↓
Download SKILL.md
```

**AI generates, proposes repairs, and executes instructions. Python enforces the schema, validates the draft, decides whether repair is necessary, and assembles `SKILL.md`. The AI never decides whether its own output is valid.**

If repair fails after two attempts, SkillSmith returns validation errors instead of an assembled skill. Invalid skills cannot be executed.

## Features

- Natural-language workflow → structured Agent Skill using local open-weight AI.
- Schema-constrained generation through Ollama and Pydantic.
- Deterministic validation and AI-assisted repair, with a maximum of two attempts.
- Visible validation status and before/after repair history.
- Deterministic `SKILL.md` assembly, copying, and client-side download.
- Interactive skill testing with sample input and copyable results.
- A responsive single-page interface; no frontend build tools.
- No cloud AI API or paid API key required. With the default local configuration, inputs stay on your machine; inference can run offline after dependencies and model weights are downloaded.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, PyYAML, httpx |
| AI | Ollama, Qwen2.5 3B |
| Frontend | HTML, CSS, vanilla JavaScript |
| Testing | pytest |

## Run Locally

Requirements: **Python 3.10+** and [Ollama](https://ollama.com/download). Final verification used Python 3.14 on macOS.

```bash
git clone https://github.com/Zoraiz03/HACKTOBERFEST.git
cd HACKTOBERFEST
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate with `.venv\Scripts\activate` instead. Install Ollama from the official link above, then start it if it is not already running:

```bash
ollama serve
```

Keep Ollama running. In another terminal, download the model:

```bash
ollama pull qwen2.5:3b
```

The supplied `.env.example` contains:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5:3b
```

From the project directory, with the virtual environment active:

```bash
python run.py
```

Open **http://localhost:8000**. Health check: http://localhost:8000/health. API documentation: http://localhost:8000/docs.

The development entry point binds to `0.0.0.0:8000`. For loopback-only access, use `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` instead.

## Demo Example

Click **Meeting Notes Example**, or enter this workflow:

```text
Read meeting notes and extract decisions, action items, owners, and deadlines.
```

Click **Generate Agent Skill** and review the validation status and generated `SKILL.md`. Paste this sample input into **Test your skill**:

```text
Product planning meeting:
Sarah will finish the landing page by Friday.
Ali will fix the login bug by tomorrow.
The team decided to launch the beta next Monday.
```

Click **Run Skill**. The result should identify Sarah's landing-page task due Friday, Ali's login-bug task due tomorrow, and the beta-launch decision for next Monday. Exact formatting varies. Click **Download SKILL.md** to save the generated file.

## Reliability Example

```text
meeting_action_extractor
        ↓
❌ Deterministic validation: invalid_format
        ↓
AI Repair
        ↓
meeting-action-extractor
        ↓
✅ Deterministic validation passed
```

Validation is code-based: the model receives exact errors and proposes corrections, which Python checks again. The implemented rules cover name format and length, description presence and length, and nonblank instructions; directory-name matching is checked when a directory is supplied. Repair history stores validation errors and structured before/after drafts, not model reasoning.

These checks improve structural reliability. They do not guarantee that generated instructions or execution results are semantically correct; test the skill with representative input.

## Testing

```bash
python -m pytest tests/ -q
```

**42 tests passing** in final verification. Tests cover assembly, validation, structured-output requests, bounded repair, API contracts, and skill execution, with the AI boundary mocked. The complete generation → validation → execution → download flow has also been verified with local Qwen through the browser.

Optional live generation/repair verification:

```bash
python -m scripts.verify_step4
```

This command requires local Ollama and `qwen2.5:3b`.

## Open Source / Model

SkillSmith application code is licensed under the [MIT License](LICENSE).

The exact configured Ollama identifier is [`qwen2.5:3b`](https://ollama.com/library/qwen2.5:3b). The official [`Qwen/Qwen2.5-3B-Instruct` model card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) lists **`qwen-research`**. Its [Qwen Research License Agreement](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) permits non-commercial research/evaluation use and requires a separate license for commercial use. The application's MIT license does not replace the model's terms. Model weights are downloaded separately and are not included in this repository.

## Team

- [Zoraiz Khan](https://github.com/Zoraiz03)
- [NaimaImtiaz23](https://github.com/NaimaImtiaz23)
