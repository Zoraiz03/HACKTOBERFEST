"""
SkillSmith — Skill Generator Service

Takes a natural language workflow description and uses the local Ollama model
to produce a structured skill definition (name, description, instructions, example).

AI prompting and JSON parsing logic are isolated here so judges can inspect them easily.
"""

import json
import logging
from pydantic import ValidationError

from app.ai import generate
from app.models import SkillGenerateResponse

logger = logging.getLogger("skillsmith.generator")

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
    """Validate structured skill JSON against Pydantic schema with normalization."""
    # Fast path: direct strict JSON validation
    try:
        return SkillGenerateResponse.model_validate_json(text)
    except ValidationError:
        pass

    # If direct validation fails, check if text is valid JSON dict needing field normalization
    try:
        data = json.loads(text)
    except Exception:
        # Re-raise standard ValidationError from Pydantic on the raw text
        return SkillGenerateResponse.model_validate_json(text)

    if isinstance(data, dict):
        if isinstance(data.get("instructions"), list):
            data["instructions"] = "\n".join(str(step) for step in data["instructions"])
        if isinstance(data.get("example"), list) and data["example"]:
            data["example"] = data["example"][0]
        elif "examples" in data and "example" not in data:
            ex = data["examples"]
            data["example"] = ex[0] if isinstance(ex, list) and ex else ex
        if isinstance(data.get("example"), dict):
            ex_obj = data["example"]
            if "input" not in ex_obj and "user_input" in ex_obj:
                ex_obj["input"] = str(ex_obj["user_input"])
            if "output" not in ex_obj and "expected_output" in ex_obj:
                ex_obj["output"] = str(ex_obj["expected_output"])

    return SkillGenerateResponse.model_validate(data)


async def generate_skill(workflow: str) -> SkillGenerateResponse:
    """
    Generate a structured skill definition from a workflow description.

    Args:
        workflow: Natural language description of the workflow.

    Returns:
        A validated SkillGenerateResponse.

    Raises:
        OllamaError / AIError: If the AI model is unreachable or fails.
        ValueError:            If the model output is not valid JSON or fails schema validation.
    """
    prompt = _build_prompt(workflow)

    raw_response = await generate(
        prompt, schema=SkillGenerateResponse.model_json_schema()
    )
    try:
        return parse_skill_draft(raw_response)
    except ValidationError as exc:
        is_json_syntax_error = any(e.get("type") == "json_invalid" for e in exc.errors())
        if is_json_syntax_error:
            logger.error("Model returned invalid JSON syntax. Preview: %.200s", raw_response)
            raise ValueError(f"Model returned invalid JSON syntax: {exc}") from exc
        else:
            errors_summary = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in exc.errors(include_input=False, include_url=False)
            )
            logger.error("Model returned invalid schema: %s", errors_summary)
            raise ValueError(f"Model returned invalid schema: {errors_summary}") from exc
