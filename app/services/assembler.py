"""
SkillSmith — Deterministic SKILL.md Assembler

Converts a validated skill structure into Agent Skills Open Standard SKILL.md format.

IMPORTANT DESIGN DECISION:
    The AI model NEVER writes raw SKILL.md content.
    This module handles all YAML frontmatter and Markdown formatting deterministically
    in Python, ensuring spec-compliant output regardless of model quirks.
"""

import yaml

from app.models import SkillGenerateResponse


def assemble_skill_md(skill: SkillGenerateResponse) -> str:
    """
    Assemble a SKILL.md file from a structured skill definition.

    The YAML frontmatter is generated deterministically using PyYAML
    for safe serialization. The Markdown body follows Agent Skills
    Open Standard structure.

    Args:
        skill: Validated skill data (typically from AI generation).

    Returns:
        Complete SKILL.md content as a string.
    """
    # Build frontmatter with controlled key order via PyYAML.
    # sort_keys=False preserves insertion order (Python 3.7+).
    # width=1000 prevents unwanted line wrapping in long descriptions.
    frontmatter = yaml.dump(
        {"name": skill.name, "description": skill.description},
        default_flow_style=False,
        sort_keys=False,
        width=1000,
        allow_unicode=True,
    ).strip()

    # Assemble the Markdown body
    lines = [
        f"---\n{frontmatter}\n---",
        "",
        "# Instructions",
        "",
        skill.instructions,
        "",
        "## Example",
        "",
        "### Input",
        "",
        skill.example.input,
        "",
        "### Output",
        "",
        skill.example.output,
        "",  # trailing newline
    ]

    return "\n".join(lines)
