"""
SkillSmith — Validator Tests

Tests the deterministic Agent Skills validator against all specification rules.
No AI is involved in any of these tests.

Run with:
    pytest tests/test_validator.py -v
"""

from app.services.validator import validate_skill


# ===================================================================
# Helper
# ===================================================================

VALID_DESCRIPTION = (
    "Extracts decisions, owners, and deadlines from meeting notes. "
    "Use when processing meeting notes or creating action summaries."
)
VALID_INSTRUCTIONS = "1. Parse the meeting notes.\n2. Identify action items.\n3. Format output."


def _codes(result):
    """Extract error codes from a validation result for easy assertion."""
    return [e.code for e in result.errors]


# ===================================================================
# CASE 1 — VALID
# ===================================================================

def test_valid_skill():
    result = validate_skill(
        name="meeting-action-extractor",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is True
    assert result.errors == []


# ===================================================================
# CASE 2 — UNDERSCORE (invalid format)
# ===================================================================

def test_underscore_in_name():
    result = validate_skill(
        name="meeting_action_extractor",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "invalid_format" in _codes(result)


# ===================================================================
# CASE 3 — UPPERCASE (invalid format)
# ===================================================================

def test_uppercase_in_name():
    result = validate_skill(
        name="Meeting-Action-Extractor",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "invalid_format" in _codes(result)


# ===================================================================
# CASE 4 — LEADING HYPHEN
# ===================================================================

def test_leading_hyphen():
    result = validate_skill(
        name="-meeting-action",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "leading_hyphen" in _codes(result)


# ===================================================================
# CASE 5 — TRAILING HYPHEN
# ===================================================================

def test_trailing_hyphen():
    result = validate_skill(
        name="meeting-action-",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "trailing_hyphen" in _codes(result)


# ===================================================================
# CASE 6 — DOUBLE HYPHEN
# ===================================================================

def test_consecutive_hyphens():
    result = validate_skill(
        name="meeting--action",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "consecutive_hyphens" in _codes(result)


# ===================================================================
# CASE 7 — NAME TOO LONG (> 64 characters)
# ===================================================================

def test_name_too_long():
    long_name = "a" * 65
    result = validate_skill(
        name=long_name,
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert "too_long" in _codes(result)


# ===================================================================
# CASE 8 — EMPTY DESCRIPTION
# ===================================================================

def test_empty_description():
    result = validate_skill(
        name="meeting-action-extractor",
        description="",
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert any(e.field == "description" and e.code == "required" for e in result.errors)


# ===================================================================
# CASE 9 — DESCRIPTION > 1024 characters
# ===================================================================

def test_description_too_long():
    result = validate_skill(
        name="meeting-action-extractor",
        description="x" * 1025,
        instructions=VALID_INSTRUCTIONS,
    )
    assert result.valid is False
    assert any(e.field == "description" and e.code == "too_long" for e in result.errors)


# ===================================================================
# CASE 10 — EMPTY INSTRUCTIONS
# ===================================================================

def test_empty_instructions():
    result = validate_skill(
        name="meeting-action-extractor",
        description=VALID_DESCRIPTION,
        instructions="",
    )
    assert result.valid is False
    assert any(e.field == "instructions" and e.code == "required" for e in result.errors)


# ===================================================================
# CASE 11 — ACTUAL STEP 2 MODEL OUTPUT (underscores)
# Proves that AI-generated names with underscores are correctly rejected.
# ===================================================================

def test_actual_model_output_underscores():
    """
    The qwen2.5:3b model returned 'bug_report_summary_classification_and_response'
    in Step 2. This name uses underscores, which violates the Agent Skills
    naming rules. The validator MUST reject it.
    """
    result = validate_skill(
        name="bug_report_summary_classification_and_response",
        description="Summarizes a bug report, classifies severity, and drafts a response.",
        instructions="1. Read the bug report.\n2. Classify severity.\n3. Draft response.",
    )
    assert result.valid is False
    assert "invalid_format" in _codes(result)
    # Confirm the error message is helpful
    name_errors = [e for e in result.errors if e.field == "name"]
    assert len(name_errors) >= 1
    assert "lowercase" in name_errors[0].message.lower() or "hyphen" in name_errors[0].message.lower()


# ===================================================================
# CASE 12 — DIRECTORY NAME MISMATCH
# ===================================================================

def test_directory_name_mismatch():
    result = validate_skill(
        name="meeting-action-extractor",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
        dir_name="wrong-directory-name",
    )
    assert result.valid is False
    assert "directory_mismatch" in _codes(result)


# ===================================================================
# CASE 13 — DIRECTORY NAME MATCHES (should pass)
# ===================================================================

def test_directory_name_matches():
    result = validate_skill(
        name="meeting-action-extractor",
        description=VALID_DESCRIPTION,
        instructions=VALID_INSTRUCTIONS,
        dir_name="meeting-action-extractor",
    )
    assert result.valid is True
    assert result.errors == []
