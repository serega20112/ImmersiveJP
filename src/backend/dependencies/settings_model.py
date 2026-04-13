from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_SECRETS = {
    "change-me",
    "change-me-too",
    "immersjp-secret-key",
    "immersjp-session-secret",
}


def _build_database_url(
    *,
    user: str,
    password: str,
    host: str,
    port: int | str,
    database: str,
    async_mode: bool,
) -> str:
    scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def _normalize_database_url(value: str | None, *, async_mode: bool) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        raise ValueError("Database URL normalization requires a non-empty value")
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://'):]}"
    if async_mode:
        if raw_value.startswith("postgresql+asyncpg://"):
            return raw_value
        if raw_value.startswith("postgresql+psycopg://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql+psycopg://'):]}"
        if raw_value.startswith("postgresql://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql://'):]}"
        return raw_value
    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value
    if raw_value.startswith("postgresql+asyncpg://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql+asyncpg://'):]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql://'):]}"
    return raw_value


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ImmersJP"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_base_url: str = "http://127.0.0.1:8000"
    log_level: str = "INFO"

    secret_key: str
    session_secret: str
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    postgres_user: str = "immersjp"
    postgres_password: str = "immersjp"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "immersjp"
    database_url: str | None = None
    database_sync_url: str | None = None

    redis_enabled: bool = True
    redis_required: bool = False
    redis_url: str | None = "redis://localhost:6379/0"

    hf_api_token: str | None = None
    hf_model: str = "openai/gpt-oss-120b"
    hf_provider: str | None = "fireworks-ai"
    hf_cards_model: str = "openai/gpt-oss-20b"
    hf_cards_timeout_seconds: float = 20
    hf_cards_retry_attempts: int = 1
    hf_cards_max_tokens: int = 1400
    hf_cards_circuit_open_seconds: int = 180
    hf_mentor_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_mentor_timeout_seconds: float = 18
    hf_mentor_retry_attempts: int = 1
    hf_mentor_max_tokens: int = 220
    hf_speech_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_speech_timeout_seconds: float = 18
    hf_speech_retry_attempts: int = 1
    hf_speech_max_tokens: int = 420
    hf_work_review_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_work_review_timeout_seconds: float = 14
    hf_work_review_retry_attempts: int = 1
    hf_work_review_max_tokens: int = 700
    hf_api_url: str = "https://router.huggingface.co/v1/chat/completions"
    hf_timeout_seconds: float = 30
    hf_retry_attempts: int = 3
    hf_retry_backoff_seconds: float = 0.8

    llm_request_limit: int = 30
    llm_request_window_seconds: int = 3600
    api_rate_limit_enabled: bool = True
    api_rate_limit_requests: int = 240
    api_rate_limit_window_seconds: int = 60
    metrics_enabled: bool = True
    onboarding_page_cache_ttl_seconds: int = 900
    text_input_limit: int = 500
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    email_verification_expire_minutes: int = 20

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@immersjp.local"
    smtp_use_tls: bool = True

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
            raise ValueError(
                f"COOKIE_SAMESITE must be one of: {', '.join(sorted(allowed))}"
            )
        return normalized

    @field_validator(
        "llm_request_limit",
        "llm_request_window_seconds",
        "api_rate_limit_requests",
        "api_rate_limit_window_seconds",
        "onboarding_page_cache_ttl_seconds",
        "hf_cards_retry_attempts",
        "hf_cards_max_tokens",
        "hf_cards_circuit_open_seconds",
        "hf_work_review_retry_attempts",
        "hf_work_review_max_tokens",
    )
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Numeric limits must be greater than zero")
        return value

    @field_validator(
        "hf_cards_timeout_seconds",
        "hf_mentor_timeout_seconds",
        "hf_speech_timeout_seconds",
        "hf_work_review_timeout_seconds",
        "hf_timeout_seconds",
        "hf_retry_backoff_seconds",
    )
    @classmethod
    def validate_positive_floats(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Timeouts and backoff must be greater than zero")
        return value

    @model_validator(mode="after")
    def normalize_database_urls(self) -> "AppSettings":
        if not self.app_debug:
            for secret_name in ("secret_key", "session_secret"):
                secret = getattr(self, secret_name)
                if len(secret) < 16 or secret in _PLACEHOLDER_SECRETS:
                    raise ValueError(
                        f"{secret_name} is too weak for non-debug mode. Set a non-placeholder value with at least 16 characters."
                    )
        fallback_database_url = _build_database_url(
            user=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            async_mode=False,
        )
        raw_database_url = self.database_url or self.database_sync_url or fallback_database_url
        self.database_url = _normalize_database_url(
            self.database_url or raw_database_url,
            async_mode=True,
        )
        self.database_sync_url = _normalize_database_url(
            self.database_sync_url or raw_database_url,
            async_mode=False,
        )
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


Settings = get_settings()
