from __future__ import annotations

import pytest

from src.backend.dependencies.settings_model import AppSettings


def test_settings_normalize_database_urls():
    settings = AppSettings(
        app_debug=False,
        secret_key="x" * 24,
        session_secret="y" * 24,
        database_url="postgresql://db-user:db-pass@db-host:5432/immersjp",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://db-user:db-pass@db-host:5432/immersjp"
    )
    assert settings.database_sync_url == (
        "postgresql+psycopg://db-user:db-pass@db-host:5432/immersjp"
    )


def test_settings_build_database_urls_from_postgres_fields():
    settings = AppSettings(
        app_debug=False,
        secret_key="x" * 24,
        session_secret="y" * 24,
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


def test_settings_preserve_explicit_database_sync_url():
    settings = AppSettings(
        app_debug=False,
        secret_key="x" * 24,
        session_secret="y" * 24,
        database_sync_url="postgresql://db-user:db-pass@postgres:5432/immersjp",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://db-user:db-pass@postgres:5432/immersjp"
    )
    assert settings.database_sync_url == (
        "postgresql+psycopg://db-user:db-pass@postgres:5432/immersjp"
    )


def test_settings_reject_weak_secrets_outside_debug():
    with pytest.raises(ValueError):
        AppSettings(
            app_debug=False,
            secret_key="change-me",
            session_secret="change-me-too",
        )


def test_settings_allow_placeholder_secrets_in_debug():
    settings = AppSettings(
        app_debug=True,
        secret_key="change-me",
        session_secret="change-me-too",
    )

    assert settings.secret_key == "change-me"
    assert settings.session_secret == "change-me-too"
