"""
SkillSmith — Assembler Tests

Tests the deterministic SKILL.md assembler output format.
Verifies that the assembled content follows Agent Skills Open Standard.

Run with:
    pytest tests/test_assembler.py -v
"""

from app.models import SkillGenerateResponse, SkillExample
from app.services.assembler import assemble_skill_md


VALID_SKILL = SkillGenerateResponse(
    name="meeting-action-extractor",
    description=(
        "Extracts decisions, owners, and deadlines from meeting notes. "
        "Use when processing meeting notes or creating action summaries."
    ),
    instructions=(
        "1. Parse the provided meeting notes or transcript.\n"
        "2. Identify all decisions made during the meeting.\n"
        "3. Extract action items with assigned owners and deadlines.\n"
        "4. Format the output as a structured summary."
    ),
    example=SkillExample(
        input="Meeting notes from Q3 planning: John will deliver the API by Oct 15.",
        output="Action: Deliver API | Owner: John | Deadline: Oct 15",
    ),
)


def test_assembled_has_yaml_frontmatter():
    """SKILL.md must start with --- and contain a closing ---."""
    md = assemble_skill_md(VALID_SKILL)
    lines = md.split("\n")
    assert lines[0] == "---", "Must start with YAML frontmatter delimiter"
    # Find closing delimiter (skip the first ---)
    assert "---" in lines[1:], "Must have closing YAML frontmatter delimiter"


def test_assembled_contains_name():
    """YAML frontmatter must contain the name field."""
    md = assemble_skill_md(VALID_SKILL)
    assert "name: meeting-action-extractor" in md


def test_assembled_contains_description():
    """YAML frontmatter must contain the description field."""
    md = assemble_skill_md(VALID_SKILL)
    assert "Extracts decisions, owners, and deadlines" in md


def test_assembled_contains_instructions():
    """Body must contain the instructions."""
    md = assemble_skill_md(VALID_SKILL)
    assert "# Instructions" in md
    assert "Parse the provided meeting notes" in md


def test_assembled_contains_example_input():
    """Body must contain the example input."""
    md = assemble_skill_md(VALID_SKILL)
    assert "### Input" in md
    assert "Q3 planning" in md


def test_assembled_contains_example_output():
    """Body must contain the example output."""
    md = assemble_skill_md(VALID_SKILL)
    assert "### Output" in md
    assert "Deliver API" in md


def test_assembled_full_structure():
    """Verify the complete assembled SKILL.md structure."""
    md = assemble_skill_md(VALID_SKILL)
    # Must have all required sections in order
    sections = ["---", "name:", "description:", "---", "# Instructions", "## Example", "### Input", "### Output"]
    for section in sections:
        assert section in md, f"Missing required section: {section}"
