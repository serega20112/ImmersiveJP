from __future__ import annotations

from email_validator import EmailNotValidError, validate_email


def normalize_email(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        raise ValueError("Email is required")
    try:
        return validate_email(normalized, check_deliverability=False).normalized
    except EmailNotValidError as error:
        raise ValueError(str(error)) from error
