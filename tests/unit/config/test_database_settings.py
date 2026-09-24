"""Юнит-тесты настроек базы данных: нормализация URL и сборка по умолчанию."""

import pytest

from src.config.database import (
    DatabaseSettings,
    _build_database_url,
    _normalize_database_url,
)


class TestNormalizeDatabaseUrl:
    """Группа тестов приведения URL к нужному драйверу."""

    @pytest.mark.parametrize(
        "raw",
        [
            "postgresql+asyncpg://u:p@h:5432/db",
            "postgresql://u:p@h:5432/db",
            "postgresql+psycopg://u:p@h:5432/db",
            "postgres://u:p@h:5432/db",
        ],
        ids=["already-async", "plain", "psycopg", "legacy-postgres"],
    )
    def test_async_mode_normalizes_to_asyncpg(self, raw: str) -> None:
        """
        Тестируем: приведение URL к драйверу asyncpg.
        Отдаём: URL во всех поддерживаемых формах.
        Ожидаем: строка с префиксом postgresql+asyncpg://.
        """
        assert _normalize_database_url(raw, async_mode=True).startswith("postgresql+asyncpg://")

    @pytest.mark.parametrize(
        "raw",
        [
            "postgresql+psycopg://u:p@h:5432/db",
            "postgresql://u:p@h:5432/db",
            "postgresql+asyncpg://u:p@h:5432/db",
        ],
        ids=["already-sync", "plain", "async-source"],
    )
    def test_sync_mode_normalizes_to_psycopg(self, raw: str) -> None:
        """
        Тестируем: приведение URL к драйверу psycopg.
        Отдаём: URL в разных формах.
        Ожидаем: строка с префиксом postgresql+psycopg://.
        """
        assert _normalize_database_url(raw, async_mode=False).startswith("postgresql+psycopg://")

    def test_rejects_empty_value(self) -> None:
        """
        Тестируем: нормализацию пустого значения.
        Отдаём: None и пустую строку.
        Ожидаем: ValueError.
        """
        with pytest.raises(ValueError):
            _normalize_database_url(None, async_mode=True)
        with pytest.raises(ValueError):
            _normalize_database_url("   ", async_mode=False)

    def test_unknown_scheme_kept_as_is(self) -> None:
        """
        Тестируем: нестандартную схему.
        Отдаём: URL с неизвестной схемой.
        Ожидаем: строка возвращается без изменений.
        """
        assert _normalize_database_url("sqlite:///:memory:", async_mode=True) == "sqlite:///:memory:"


class TestBuildDatabaseUrl:
    """Группа тестов сборки URL из компонентов."""

    def test_builds_sync_url_by_parts(self) -> None:
        """
        Тестируем: сборку URL из учётных данных.
        Отдаём: пользователь, пароль, хост, порт и базу.
        Ожидаем: строка postgresql+psycopg:// с переданными частями.
        """
        url = _build_database_url(user="u", password="p", host="h", port=5432, database="db", async_mode=False)

        assert url == "postgresql+psycopg://u:p@h:5432/db"


class TestDatabaseSettings:
    """Группа тестов модельных настроек БД."""

    def test_defaults_build_fallback_urls(self) -> None:
        """
        Тестируем: автосборку URL при отсутствии переданных.
        Отдаём: DatabaseSettings без URL.
        Ожидаем: оба URL заполнены из postgres_* полей с корректными схемами.
        """
        settings_model = DatabaseSettings(postgres_user="alice", postgres_password="s3cret", postgres_host="db", postgres_port=5433, postgres_db="immersjp_test")

        assert settings_model.database_url.startswith("postgresql+asyncpg://alice:s3cret@db:5433/immersjp_test")
        assert settings_model.database_sync_url.startswith("postgresql+psycopg://alice:s3cret@db:5433/immersjp_test")

    def test_explicit_async_url_is_normalized(self) -> None:
        """
        Тестируем: нормализацию явно переданного legacy-URL.
        Отдаём: database_url со схемой postgres://.
        Ожидаем: database_url переписан в asyncpg-схему.
        """
        settings_model = DatabaseSettings(database_url="postgres://u:p@h:5432/db")

        assert settings_model.database_url.startswith("postgresql+asyncpg://")

    def test_pool_size_accepts_any_int(self) -> None:
        """
        Тестируем: отсутствие ограничения на знак размера пула.
        Отдаём: pool_size=-1.
        Ожидаем: значение сохранено как есть (валидация знака не задана).
        """
        settings_model = DatabaseSettings(pool_size=-1)

        assert settings_model.pool_size == -1
