"""Exercise HTTP contracts and the full pipeline with a mocked AI boundary."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.ollama_client import OllamaError
from app.models import GeneratedSkillDraft
from app.services import generator, repair

DRAFT = GeneratedSkillDraft(
    name="meeting-action-extractor", description="Extract meeting actions.",
    instructions="1. Read notes.\n2. Extract actions.",
    example={"input": "Ship Friday.", "output": "Ship | Friday"},
)
WORKFLOW = {"workflow": "Read meeting notes and extract decisions, action items, owners, and deadlines."}
client = TestClient(app)


def test_existing_endpoints(monkeypatch):
    ai = AsyncMock(return_value=DRAFT.model_dump_json())
    monkeypatch.setattr(generator, "generate", ai)
    assert client.get("/health").json()["status"] == "ok"
    generated = client.post("/api/generate", json=WORKFLOW)
    assert generated.status_code == 200 and generated.json() == DRAFT.model_dump()
    assembled = client.post("/api/assemble", json=generated.json())
    assert assembled.status_code == 200 and assembled.json()["validation"]["valid"]
    invalid = DRAFT.model_copy(update={"name": "bad_name"})
    assert not client.post("/api/assemble", json=invalid.model_dump()).json()["validation"]["valid"]
    assert ai.call_args.kwargs["schema"] == DRAFT.model_json_schema()
    prompt = ai.call_args.args[0]
    assert "snake_case" not in prompt and "NO underscores" in prompt
    assert "64" in prompt and "no consecutive hyphens" in prompt


@pytest.mark.parametrize("invalid,repair_success", [(False, True), (True, True), (True, False)])
def test_pipeline_endpoint(monkeypatch, invalid, repair_success):
    draft = DRAFT.model_copy(update={"name": "bad_name"}) if invalid else DRAFT
    monkeypatch.setattr(generator, "generate", AsyncMock(return_value=draft.model_dump_json()))
    ai = AsyncMock(return_value=(DRAFT if repair_success else draft).model_dump_json())
    monkeypatch.setattr(repair, "generate", ai)
    response = client.post("/api/generate-and-repair", json=WORKFLOW)
    assert response.status_code == 200
    data = response.json()
    assert data["initial_valid"] == (not invalid)
    assert data["final_valid"] == repair_success
    assert ai.await_count == (0 if not invalid else 1 if repair_success else 2)
    assert bool(data["skill_md"]) == repair_success
    assert len(data["repair_attempts"]) == ai.await_count


@pytest.mark.parametrize("path", ["/api/generate", "/api/generate-and-repair"])
def test_api_errors(monkeypatch, path):
    monkeypatch.setattr(generator, "generate", AsyncMock(side_effect=OllamaError("Unavailable")))
    assert client.post(path, json=WORKFLOW).status_code == 503
    monkeypatch.setattr(generator, "generate", AsyncMock(return_value='Prose before {"name":"x"}'))
    assert client.post(path, json=WORKFLOW).status_code == 422
    assert client.post(path, json={"workflow": "short"}).status_code == 422


def test_repair_transport_error(monkeypatch):
    invalid = DRAFT.model_copy(update={"name": "bad_name"})
    monkeypatch.setattr(generator, "generate", AsyncMock(return_value=invalid.model_dump_json()))
    monkeypatch.setattr(repair, "generate", AsyncMock(side_effect=OllamaError("Unavailable")))
    assert client.post("/api/generate-and-repair", json=WORKFLOW).status_code == 503
