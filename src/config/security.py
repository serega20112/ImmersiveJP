from pydantic import field_validator

from src.config.base import BaseAppSettings

_PLACEHOLDER_SECRETS = {
    "change-me",
    "change-me-too",
    "immersjp-secret-key",
    "immersjp-session-secret",
}


class SecuritySettings(BaseAppSettings):
    """Безопасность / аутентификация / cookies."""

    secret_key: str = "change-me"
    session_secret: str = "change-me-too"

    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    session_cookie_name: str = "immersjp_session"
    csrf_session_key: str = "csrf_token"
    csrf_field_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"

    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    email_verification_expire_minutes: int = 20

    model_config = BaseAppSettings.model_config

    @field_validator("secret_key", "session_secret")
    @classmethod
    def normalize_secret(cls, value: str) -> str:
        return value.strip()

    @field_validator("cookie_samesite")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"lax", "strict", "none"}
        if normalized not in allowed:
            raise ValueError(f"COOKIE_SAMESITE must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator(
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "email_verification_expire_minutes",
    )
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Numeric limits must be greater than zero")
        return value
