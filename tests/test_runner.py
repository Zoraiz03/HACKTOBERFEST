"""Essential execution checks through /api/run, mocking only Ollama."""
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services import runner

client = TestClient(app)
SKILL = {
    "name": "meeting-action-extractor",
    "description": "Extract actions, owners, and deadlines from meeting notes.",
    "instructions": "1. Read the notes.\n2. Return each action with its owner and deadline.",
    "example": {"input": "Sarah will ship Friday.", "output": "Sarah | ship | Friday"},
}


def test_valid_skill_executes(monkeypatch):
    ai = AsyncMock(return_value="Sarah | landing page | Friday")
    monkeypatch.setattr(runner, "generate", ai)
    sample = "Sarah will finish the landing page by Friday."
    response = client.post("/api/run", json={"skill": SKILL, "input": sample})
    assert response.status_code == 200
    assert response.json() == {"output": "Sarah | landing page | Friday"}
    ai.assert_awaited_once()
    prompt = ai.call_args.args[0]
    for value in (SKILL["name"], SKILL["description"], SKILL["instructions"], sample):
        assert value in prompt


def test_invalid_skill_rejected(monkeypatch):
    ai = AsyncMock()
    monkeypatch.setattr(runner, "generate", ai)
    response = client.post("/api/run", json={
        "skill": {**SKILL, "name": "invalid_name"}, "input": "Meeting notes here.",
    })
    assert response.status_code == 422
    assert "Cannot execute invalid skill: name:" in response.json()["detail"]
    ai.assert_not_awaited()


def test_blank_input_rejected(monkeypatch):
    ai = AsyncMock()
    monkeypatch.setattr(runner, "generate", ai)
    for sample in ("", " \n\t "):
        response = client.post("/api/run", json={"skill": SKILL, "input": sample})
        assert response.status_code == 422
        assert response.json()["detail"] == "Sample input must not be blank."
    ai.assert_not_awaited()
