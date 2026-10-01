"""
SkillSmith — Pydantic Models

Data models for skill generation requests and responses.
"""

from pydantic import BaseModel, Field


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
