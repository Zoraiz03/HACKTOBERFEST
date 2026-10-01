"""
SkillSmith — Skill Generator Service

Takes a natural language workflow description and uses the local Ollama model
to produce a structured skill definition (name, description, instructions, example).

AI prompting and JSON parsing logic are isolated here so judges can inspect them easily.
"""

import json
import re

from app.ai.ollama_client import generate, OllamaError
from app.models import SkillGenerateResponse

# ---------------------------------------------------------------------------
# System prompt — instructs the model to return valid JSON only
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are SkillSmith, an AI that converts workflow descriptions into structured Agent Skills.

You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no explanation.

The JSON object must have exactly these fields:
{
  "name": "short_snake_case_name",
  "description": "One sentence describing what this skill does.",
  "instructions": "Clear step-by-step instructions that an AI agent should follow to execute this skill. Use numbered steps.",
  "example": {
    "input": "A realistic example input a user would provide.",
    "output": "The expected output the skill would produce for that input."
  }
}

Rules:
- "name" must be lowercase snake_case, max 50 characters.
- "description" must be one clear sentence.
- "instructions" must be detailed, numbered steps.
- "example.input" and "example.output" must be realistic and concrete.
- Return ONLY the JSON object. Nothing else."""


def _build_prompt(workflow: str) -> str:
    """Build the full prompt from the system prompt and user workflow."""
    return f"""{SYSTEM_PROMPT}

User workflow description:
{workflow}

Respond with ONLY the JSON object:"""


def _extract_json(text: str) -> dict:
    """
    Extract a JSON object from model output.

    Handles common model quirks:
    - JSON wrapped in ```json ... ``` code fences
    - Leading/trailing whitespace or text around the JSON
    """
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # Try to find the outermost { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if not brace_match:
        raise ValueError("No JSON object found in model response")

    return json.loads(brace_match.group())


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

    raw_response = await generate(prompt)

    try:
        data = _extract_json(raw_response)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"Model returned invalid JSON. Parse error: {e}\n"
            f"Raw response: {raw_response[:500]}"
        )

    # Validate through Pydantic — ensures all required fields are present
    try:
        skill = SkillGenerateResponse(**data)
    except Exception as e:
        raise ValueError(
            f"Model JSON is missing required fields. Validation error: {e}\n"
            f"Parsed data: {json.dumps(data, indent=2)[:500]}"
        )

    return skill
