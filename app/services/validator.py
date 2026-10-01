"""
SkillSmith — Deterministic Agent Skills Validator

Validates skill definitions against the Agent Skills Open Standard.

This is PURE PYTHON validation — no AI is involved.

Validated rules (MVP):
    NAME:
        - Required, 1–64 characters
        - Only lowercase a-z, digits 0-9, hyphens
        - Must not start/end with a hyphen
        - Must not contain consecutive hyphens (--)
        - Must match parent directory name (when provided)
    DESCRIPTION:
        - Required, 1–1024 characters
    INSTRUCTIONS:
        - Required, must not be empty
"""

import re

from app.models import SkillValidationError, SkillValidationResult


# Only lowercase ASCII letters, digits, and single hyphens
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 1024


def validate_skill(
    name: str,
    description: str,
    instructions: str,
    dir_name: str | None = None,
) -> SkillValidationResult:
    """
    Validate a skill definition against the Agent Skills Open Standard.

    This function performs deterministic, rule-based validation.
    It does NOT call any AI model.

    Args:
        name:         Skill name to validate.
        description:  Skill description to validate.
        instructions: Skill instructions body to validate.
        dir_name:     Optional skill directory name that must match the name.

    Returns:
        SkillValidationResult with a valid flag and a list of errors.
    """
    errors: list[SkillValidationError] = []

    # ------------------------------------------------------------------
    # Name validation
    # ------------------------------------------------------------------
    if not name or not name.strip():
        errors.append(SkillValidationError(
            field="name",
            code="required",
            message="Name is required and must not be empty.",
        ))
    else:
        if len(name) > NAME_MAX_LENGTH:
            errors.append(SkillValidationError(
                field="name",
                code="too_long",
                message=f"Name must be at most {NAME_MAX_LENGTH} characters (got {len(name)}).",
            ))

        if not NAME_PATTERN.match(name):
            errors.append(SkillValidationError(
                field="name",
                code="invalid_format",
                message="Name may contain only lowercase letters (a-z), digits (0-9), and hyphens (-).",
            ))

        if name.startswith("-"):
            errors.append(SkillValidationError(
                field="name",
                code="leading_hyphen",
                message="Name must not start with a hyphen.",
            ))

        if name.endswith("-"):
            errors.append(SkillValidationError(
                field="name",
                code="trailing_hyphen",
                message="Name must not end with a hyphen.",
            ))

        if "--" in name:
            errors.append(SkillValidationError(
                field="name",
                code="consecutive_hyphens",
                message="Name must not contain consecutive hyphens (--).",
            ))

    # ------------------------------------------------------------------
    # Description validation
    # ------------------------------------------------------------------
    if not description or not description.strip():
        errors.append(SkillValidationError(
            field="description",
            code="required",
            message="Description is required and must not be empty.",
        ))
    else:
        if len(description) > DESCRIPTION_MAX_LENGTH:
            errors.append(SkillValidationError(
                field="description",
                code="too_long",
                message=(
                    f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters "
                    f"(got {len(description)})."
                ),
            ))

    # ------------------------------------------------------------------
    # Instructions / body validation
    # ------------------------------------------------------------------
    if not instructions or not instructions.strip():
        errors.append(SkillValidationError(
            field="instructions",
            code="required",
            message="Instructions body must not be empty.",
        ))

    # ------------------------------------------------------------------
    # Directory name match
    # ------------------------------------------------------------------
    if dir_name is not None and name and name.strip():
        if dir_name != name:
            errors.append(SkillValidationError(
                field="name",
                code="directory_mismatch",
                message=f"Skill name '{name}' does not match directory name '{dir_name}'.",
            ))

    return SkillValidationResult(
        valid=len(errors) == 0,
        errors=errors,
    )
