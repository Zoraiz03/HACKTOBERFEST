"""
SkillSmith — Skill Generator Service

Takes a natural language workflow description and uses the local Ollama model
to produce a structured skill definition (name, description, instructions, example).

AI prompting and JSON parsing logic are isolated here so judges can inspect them easily.
"""

from pydantic import ValidationError

from app.ai.ollama_client import generate
from app.models import SkillGenerateResponse

# ---------------------------------------------------------------------------
# System prompt — instructs the model to return valid JSON only
# ---------------------------------------------------------------------------
NAME_RULES = (
    "Name must be kebab-case / lowercase hyphen-separated, 1–64 characters: "
    "lowercase a-z, digits 0-9 and hyphens only; NO underscores, NO spaces, "
    "NO uppercase, no leading/trailing hyphen, no consecutive hyphens. "
    "Examples: meeting-action-extractor, bug-report-analyzer, lecture-revision-generator."
)

SYSTEM_PROMPT = """You are SkillSmith, an AI that converts workflow descriptions into structured Agent Skills.

You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no explanation.

The JSON object must have exactly these fields:
{
  "name": "short-kebab-case-name",
  "description": "One sentence describing what this skill does.",
  "instructions": "Clear step-by-step instructions that an AI agent should follow to execute this skill. Use numbered steps.",
  "example": {
    "input": "A realistic example input a user would provide.",
    "output": "The expected output the skill would produce for that input."
  }
}

Rules:
- {name_rules}
- "description" must be one clear sentence.
- "instructions" must be detailed, numbered steps.
- "example.input" and "example.output" must be realistic and concrete.
- Return ONLY the JSON object. Nothing else.""".replace("{name_rules}", NAME_RULES)


def _build_prompt(workflow: str) -> str:
    """Build the full prompt from the system prompt and user workflow."""
    return f"""{SYSTEM_PROMPT}

User workflow description:
{workflow}

Respond with ONLY the JSON object:"""


def parse_skill_draft(text: str) -> SkillGenerateResponse:
    """Accept only the structured JSON schema, never extract JSON from prose."""
    return SkillGenerateResponse.model_validate_json(text)


async def generate_skill(workflow: str) -> SkillGenerateResponse:
    """
    Generate a structured skill definition from a workflow description.

    Args:
        workflow: Natural language description of the workflow.

    Returns:
        A validated SkillGenerateResponse.

    Raises:
        OllamaError: If the AI model is unreachable or fails.
        ValueError:  If the model output is not valid JSON or fails validation.
    """
    prompt = _build_prompt(workflow)

    raw_response = await generate(
        prompt, schema=SkillGenerateResponse.model_json_schema()
    )
    try:
        return parse_skill_draft(raw_response)
    except ValidationError as exc:
        raise ValueError("Model returned invalid structured skill JSON.") from exc
