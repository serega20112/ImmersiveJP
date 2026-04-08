from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _build_default_database_url(*, async_mode: bool) -> str:
    user = os.getenv("POSTGRES_USER", "immersjp")
    password = os.getenv("POSTGRES_PASSWORD", "immersjp")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "immersjp")
    scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def _normalize_database_url(value: str | None, *, async_mode: bool) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return _build_default_database_url(async_mode=async_mode)
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://') :]}"
    if async_mode:
        if raw_value.startswith("postgresql+asyncpg://"):
            return raw_value
        if raw_value.startswith("postgresql+psycopg://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql+psycopg://') :]}"
        if raw_value.startswith("postgresql://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql://') :]}"
        return raw_value
    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value
    if raw_value.startswith("postgresql+asyncpg://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql+asyncpg://') :]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql://') :]}"
    return raw_value


class Settings:
    app_name: str = os.getenv("APP_NAME", "ImmersJP")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    app_debug: bool = os.getenv("APP_DEBUG", "0") == "1"
    app_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    secret_key: str = os.getenv("SECRET_KEY", "immersjp-secret-key")
    session_secret: str = os.getenv("SESSION_SECRET", "immersjp-session-secret")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "0") == "1"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")
    database_url: str = _normalize_database_url(
        os.getenv("DATABASE_URL"), async_mode=True
    )
    database_sync_url: str = _normalize_database_url(
        os.getenv("DATABASE_URL"),
        async_mode=False,
    )
    redis_enabled: bool = os.getenv("REDIS_ENABLED", "1") == "1"
    redis_required: bool = os.getenv("REDIS_REQUIRED", "0") == "1"
    redis_url: str | None = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    hf_api_token: str | None = os.getenv("HF_API_TOKEN") or None
    hf_model: str = os.getenv("HF_MODEL", "openai/gpt-oss-120b")
    hf_provider: str | None = os.getenv("HF_PROVIDER", "fireworks-ai") or None
    hf_mentor_model: str = os.getenv(
        "HF_MENTOR_MODEL",
        "openai/gpt-oss-20b:fireworks-ai",
    )
    hf_mentor_timeout_seconds: float = float(
        os.getenv("HF_MENTOR_TIMEOUT_SECONDS", "18")
    )
    hf_mentor_retry_attempts: int = int(
        os.getenv("HF_MENTOR_RETRY_ATTEMPTS", "1")
    )
    hf_mentor_max_tokens: int = int(
        os.getenv("HF_MENTOR_MAX_TOKENS", "220")
    )
    hf_api_url: str = os.getenv(
        "HF_API_URL",
        "https://router.huggingface.co/v1/chat/completions",
    )
    hf_timeout_seconds: float = float(os.getenv("HF_TIMEOUT_SECONDS", "30"))
    hf_retry_attempts: int = int(os.getenv("HF_RETRY_ATTEMPTS", "3"))
    hf_retry_backoff_seconds: float = float(
        os.getenv("HF_RETRY_BACKOFF_SECONDS", "0.8")
    )
    llm_request_limit: int = int(os.getenv("LLM_REQUEST_LIMIT", "30"))
    llm_request_window_seconds: int = int(
        os.getenv("LLM_REQUEST_WINDOW_SECONDS", "3600")
    )
    text_input_limit: int = int(os.getenv("TEXT_INPUT_LIMIT", "500"))
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    email_verification_expire_minutes: int = int(
        os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "20")
    )
    smtp_host: str | None = os.getenv("SMTP_HOST") or None
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME") or None
    smtp_password: str | None = os.getenv("SMTP_PASSWORD") or None
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@immersjp.local")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "1") == "1"
