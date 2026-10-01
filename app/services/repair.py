"""Bounded AI corrections, with Python validation as the sole authority."""

import json

from pydantic import ValidationError

from app.ai import generate
from app.models import (
    GeneratedSkillDraft, GenerateAndRepairResponse, RepairAttempt,
    SkillValidationError, SkillValidationResult,
)
from app.services.assembler import assemble_skill_md
from app.services.generator import NAME_RULES, generate_skill, parse_skill_draft
from app.services.validator import validate_skill

MAX_REPAIR_ATTEMPTS = 2


def validate_draft(skill: GeneratedSkillDraft) -> SkillValidationResult:
    return validate_skill(skill.name, skill.description, skill.instructions)


def _repair_prompt(skill: GeneratedSkillDraft, errors: list[SkillValidationError]) -> str:
    prompt = (
        "This Agent Skill draft failed deterministic validation.\n"
        f"Original draft:\n{skill.model_dump_json()}\n"
        f"Validation errors:\n{json.dumps([e.model_dump() for e in errors])}\n"
        "Correct only the fields responsible for these errors. Preserve the workflow intent "
        "and all unaffected fields. Return ONLY JSON with the same schema: "
        "name, description, instructions (strings), example (input and output strings). "
        "No explanations or validation claims.\n"
    )
    if any(error.field == "name" for error in errors):
        prompt += NAME_RULES
    return prompt


async def repair_skill(skill: GeneratedSkillDraft) -> GenerateAndRepairResponse:
    """Validate a draft and make at most two repair calls; never assemble invalid drafts.

    Malformed JSON/schema responses consume an attempt and leave the last typed
    draft unchanged. Their history has after=null and sanitized schema errors.
    Transport failures propagate to the API's existing Ollama error handling.
    """
    current = skill.model_copy(deep=True)
    validation = validate_draft(current)
    initial_valid = validation.valid
    history = []
    errors = validation.errors

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        if validation.valid:
            break
        before = current.model_copy(deep=True)
        errors_before = list(errors)
        raw = await generate(
            _repair_prompt(before, errors_before),
            schema=GeneratedSkillDraft.model_json_schema(),
        )
        try:
            after = parse_skill_draft(raw)
        except ValidationError as exc:
            # Do not retain raw model prose or Pydantic's input values.
            schema_errors = [
                SkillValidationError(
                    field=".".join(str(part) for part in error["loc"]) or "draft",
                    code=error["type"],
                    message=error["msg"],
                )
                for error in exc.errors(include_input=False, include_url=False)
            ]
            after = None
            errors = validation.errors + schema_errors
        else:
            current = after
            validation = validate_draft(current)
            errors = validation.errors
        history.append(RepairAttempt(
            attempt=attempt, errors_before=errors_before, before=before,
            after=after, valid_after=after is not None and validation.valid,
            errors_after=list(errors),
        ))

    return GenerateAndRepairResponse(
        initial_valid=initial_valid, repair_attempts=history,
        final_valid=validation.valid, final_skill=current,
        final_validation=validation,
        skill_md=assemble_skill_md(current) if validation.valid else None,
    )


async def generate_and_repair(workflow: str) -> GenerateAndRepairResponse:
    return await repair_skill(await generate_skill(workflow))
