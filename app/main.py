"""
SkillSmith — FastAPI Application

Endpoints:
  GET  /health        — Health check
  POST /api/generate  — Generate a structured skill from a workflow description
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.models import SkillGenerateRequest, SkillGenerateResponse
from app.services import generate_skill
from app.ai.ollama_client import OllamaError

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

# ---------------------------------------------------------------------------
# Static files & frontend
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the placeholder frontend page."""
    return FileResponse("app/templates/index.html")


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

