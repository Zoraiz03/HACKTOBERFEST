"""Execute a deterministically validated skill using the AI provider."""

from app.ai import generate
from app.models import GeneratedSkillDraft
from app.services.validator import validate_skill


async def run_skill(skill: GeneratedSkillDraft, input_text: str) -> str:
    validation = validate_skill(skill.name, skill.description, skill.instructions)
    if not validation.valid:
        errors = "; ".join(f"{e.field}: {e.message}" for e in validation.errors)
        raise ValueError(f"Cannot execute invalid skill: {errors}")
    if not input_text.strip():
        raise ValueError("Sample input must not be blank.")

    prompt = (
        "You are executing the following Agent Skill.\n\n"
        f"Skill name:\n{skill.name}\n\n"
        f"Skill description:\n{skill.description}\n\n"
        f"Follow these instructions carefully:\n{skill.instructions}\n\n"
        "Return only the result of executing the skill on the user's input.\n\n"
        f"USER INPUT:\n{input_text}"
    )
    return await generate(prompt)
