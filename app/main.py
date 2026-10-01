"""
SkillSmith — FastAPI Application

Endpoints:
  GET  /health        — Health check
  POST /api/generate  — Generate a structured skill from a workflow description
  POST /api/assemble  — Assemble SKILL.md and validate against Agent Skills spec
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.models import (
    SkillGenerateRequest,
    SkillGenerateResponse,
    AssembleResponse,
    GenerateAndRepairResponse,
    SkillRunRequest,
    SkillRunResponse,
)
from app.services import generate_skill, assemble_skill_md, validate_skill
from app.ai.ollama_client import OllamaError
from app.services.repair import generate_and_repair
from app.services.runner import run_skill

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

# ---------------------------------------------------------------------------
# Static files & frontend
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the placeholder frontend page."""
    return FileResponse(str(TEMPLATE_FILE))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "project": APP_NAME,
    }


# ---------------------------------------------------------------------------
# Skill generation
# ---------------------------------------------------------------------------
@app.post("/api/generate", response_model=SkillGenerateResponse)
async def api_generate_skill(request: SkillGenerateRequest):
    """
    Generate a structured Agent Skill from a natural language workflow.

    Returns a JSON object with: name, description, instructions, example.
    """
    try:
        skill = await generate_skill(request.workflow)
        return skill
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# Skill assembly + validation
# ---------------------------------------------------------------------------
@app.post("/api/assemble", response_model=AssembleResponse)
async def api_assemble_skill(skill: SkillGenerateResponse):
    """
    Assemble a SKILL.md from a structured skill draft and validate it
    against the Agent Skills Open Standard.

    The SKILL.md is built deterministically in Python — the AI model
    never writes raw YAML or Markdown.

    Returns the assembled SKILL.md content and validation result.
    """
    # Assemble SKILL.md deterministically
    skill_md = assemble_skill_md(skill)

    # Validate against Agent Skills spec (pure Python, no AI)
    validation = validate_skill(
        name=skill.name,
        description=skill.description,
        instructions=skill.instructions,
    )

    return AssembleResponse(
        skill_md=skill_md,
        validation=validation,
    )


@app.post("/api/generate-and-repair", response_model=GenerateAndRepairResponse)
async def api_generate_and_repair(request: SkillGenerateRequest):
    """Generate, validate, and repair at most twice; return auditable history."""
    try:
        return await generate_and_repair(request.workflow)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/api/run", response_model=SkillRunResponse)
async def api_run_skill(request: SkillRunRequest):
    """Execute a valid skill on sample input, without automatic repair."""
    try:
        output = await run_skill(request.skill, request.input)
        return SkillRunResponse(output=output)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
