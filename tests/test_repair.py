"""Repair behavior with the Ollama boundary mocked; no live model needed."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from app.models import GeneratedSkillDraft
from app.services import repair


@pytest.fixture
def skill():
    return GeneratedSkillDraft(
        name="meeting-action-extractor",
        description="Extract meeting decisions, actions, owners, and deadlines.",
        instructions="1. Read notes.\n2. Extract actions with owners and deadlines.",
        example={"input": "Ali will ship Friday.", "output": "Ship | Ali | Friday"},
    )


def test_already_valid(monkeypatch, skill):
    ai = AsyncMock()
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(skill))
    ai.assert_not_awaited()
    assert result.initial_valid and result.final_valid
    assert result.repair_attempts == []
    assert result.skill_md.startswith("---\n")


@pytest.mark.parametrize("updates,field,code", [
    ({"name": "meeting_action_extractor"}, "name", "invalid_format"),
    ({"name": "Meeting-Action-Extractor"}, "name", "invalid_format"),
    ({"description": ""}, "description", "required"),
    ({"description": "x" * 1025}, "description", "too_long"),
])
def test_repair_invalid_field(monkeypatch, skill, updates, field, code):
    invalid = skill.model_copy(update=updates)
    errors = repair.validate_draft(invalid).errors
    assert any(e.field == field and e.code == code for e in errors)
    ai = AsyncMock(return_value=skill.model_dump_json())
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(invalid))
    assert ai.await_count == 1
    assert not result.initial_valid and result.final_valid
    attempt = result.repair_attempts[0]
    assert attempt.errors_before == errors
    assert attempt.before == invalid and attempt.after == skill
    assert attempt.valid_after and attempt.errors_after == []
    assert result.final_skill == skill
    prompt = ai.call_args.args[0]
    assert invalid.model_dump_json() in prompt
    assert all(e.message in prompt for e in errors)
    assert ai.call_args.kwargs["schema"] == GeneratedSkillDraft.model_json_schema()
    if field == "name":
        assert "NO underscores" in prompt


def test_two_invalid_attempts_stop(monkeypatch, skill):
    invalid = skill.model_copy(update={"name": "bad_name"})
    ai = AsyncMock(return_value=invalid.model_dump_json())
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(invalid))
    assert ai.await_count == 2
    assert [a.attempt for a in result.repair_attempts] == [1, 2]
    assert not result.final_valid
    assert result.skill_md is None
    assert result.final_skill == invalid
    assert result.final_validation.errors


def test_second_attempt_uses_latest_draft(monkeypatch, skill):
    invalid = skill.model_copy(update={"name": "bad_name", "description": ""})
    partial = invalid.model_copy(update={"name": skill.name})
    ai = AsyncMock(side_effect=[partial.model_dump_json(), skill.model_dump_json()])
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(invalid))
    assert ai.await_count == 2 and result.final_valid
    assert result.repair_attempts[1].before == partial
    assert [e.field for e in result.repair_attempts[1].errors_before] == ["description"]
    assert invalid.name == "bad_name"  # original remains unchanged


@pytest.mark.parametrize("raw", [
    "Here is your skill: {}", '{"name":"fixed"}',
    '{"name":42,"description":[],"instructions":null,"example":{}}',
])
def test_malformed_output_consumes_attempts(monkeypatch, skill, raw):
    invalid = skill.model_copy(update={"name": "bad_name"})
    ai = AsyncMock(return_value=raw)
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(invalid))
    assert ai.await_count == 2 and not result.final_valid
    assert result.final_skill == invalid and result.skill_md is None
    assert all(a.after is None and not a.valid_after for a in result.repair_attempts)
    assert all(a.errors_after for a in result.repair_attempts)
    assert "Here is your skill" not in result.model_dump_json()


def test_recover_after_schema_failure(monkeypatch, skill):
    ai = AsyncMock(side_effect=['{}', skill.model_dump_json()])
    monkeypatch.setattr(repair, "generate", ai)
    result = asyncio.run(repair.repair_skill(skill.model_copy(update={"name": "bad_name"})))
    assert ai.await_count == 2 and result.final_valid
    assert result.repair_attempts[0].after is None
    assert result.repair_attempts[1].after == skill
