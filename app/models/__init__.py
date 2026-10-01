"""
SkillSmith — Pydantic Models

Data models for skill generation, assembly, and validation.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Skill generation (Step 2)
# ---------------------------------------------------------------------------

class SkillExample(BaseModel):
    """A single input/output example demonstrating the skill."""
    input: str = Field(..., description="Example user input for the skill")
    output: str = Field(..., description="Example expected output from the skill")


class SkillGenerateRequest(BaseModel):
    """Request body for POST /api/generate."""
    workflow: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the workflow to turn into a skill",
    )


class SkillGenerateResponse(BaseModel):
    """Structured skill definition returned by the AI."""
    name: str = Field(..., description="Short, descriptive skill name")
    description: str = Field(..., description="One-line description of what the skill does")
    instructions: str = Field(..., description="Step-by-step instructions for an AI agent")
    example: SkillExample = Field(..., description="One concrete input/output example")


# ---------------------------------------------------------------------------
# Validation (Step 3)
# ---------------------------------------------------------------------------

class SkillValidationError(BaseModel):
    """A single validation error with machine-readable code and human message."""
    field: str = Field(..., description="The field that failed validation")
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")


class SkillValidationResult(BaseModel):
    """Result of validating a skill against the Agent Skills Open Standard."""
    valid: bool = Field(..., description="True if all validation rules pass")
    errors: list[SkillValidationError] = Field(
        default_factory=list,
        description="List of validation errors (empty when valid)",
    )


class AssembleResponse(BaseModel):
    """Response from POST /api/assemble — assembled SKILL.md plus validation."""
    skill_md: str = Field(..., description="Assembled SKILL.md content")
    validation: SkillValidationResult = Field(..., description="Spec validation result")
