from __future__ import annotations

import pytest

from src.config.app import AppSettings
from src.config.database import DatabaseSettings
from src.config.elasticsearch import ElasticsearchSettings
from src.config.llm import LLMSettings
from src.config.rag import RAGSettings
from src.config.redis import RedisSettings
from src.config.security import SecuritySettings
from src.config.settings import Settings
from src.config.smtp import SMTPSettings


def _settings(*, app_debug: bool) -> Settings:
    return Settings(
        app=AppSettings(app_debug=app_debug),
        db=DatabaseSettings(
            postgres_user="db-user",
            postgres_password="db-pass",
            postgres_host="postgres",
            postgres_port=5432,
            postgres_db="immersjp",
        ),
        security=SecuritySettings(
            secret_key="x" * 24,
            session_secret="y" * 24,
        ),
        llm=LLMSettings(),
        rag=RAGSettings(),
        redis=RedisSettings(),
        smtp=SMTPSettings(),
        elasticsearch=ElasticsearchSettings(),
    )


def _settings_with_secrets(*, app_debug: bool, secret_key: str, session_secret: str) -> Settings:
    return Settings(
        app=AppSettings(app_debug=app_debug),
        db=DatabaseSettings(),
        security=SecuritySettings(secret_key=secret_key, session_secret=session_secret),
        llm=LLMSettings(),
        rag=RAGSettings(),
        redis=RedisSettings(),
        smtp=SMTPSettings(),
        elasticsearch=ElasticsearchSettings(),
    )


def test_database_normalize_database_urls():
    settings = DatabaseSettings(
        database_url="postgresql://db-user:db-pass@db-host:5432/immersjp",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://db-user:db-pass@db-host:5432/immersjp"
    )
    assert settings.database_sync_url == (
        "postgresql+psycopg://db-user:db-pass@db-host:5432/immersjp"
    )


def test_database_build_database_urls_from_postgres_fields():
    settings = DatabaseSettings(
        postgres_user="db-user",
        postgres_password="db-pass",
        postgres_host="postgres",
        postgres_port=5432,
        postgres_db="immersjp",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://db-user:db-pass@postgres:5432/immersjp"
    )
    assert settings.database_sync_url == (
        "postgresql+psycopg://db-user:db-pass@postgres:5432/immersjp"
    )


def test_settings_reject_weak_secrets_outside_debug():
    with pytest.raises(ValueError):
        _settings_with_secrets(
            app_debug=False,
            secret_key="change-me",
            session_secret="change-me-too",
        )


def test_settings_allow_placeholder_secrets_in_debug():
    settings = _settings_with_secrets(
        app_debug=True,
        secret_key="change-me",
        session_secret="change-me-too",
    )

    assert settings.security.secret_key == "change-me"
    assert settings.security.session_secret == "change-me-too"


def test_settings_load_uses_singleton():
    from src.config import settings as singleton

    assert isinstance(singleton, Settings)
    assert singleton.app.app_name is not None
