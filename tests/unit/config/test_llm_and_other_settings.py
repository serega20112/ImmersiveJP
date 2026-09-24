"""Юнит-тесты LLM-настроек и остальных блоков конфигурации."""

import pytest
from pydantic import ValidationError

from src.config.elasticsearch import ElasticsearchSettings
from src.config.llm import LLMSettings
from src.config.rag import RAGSettings
from src.config.redis import RedisSettings
from src.config.settings import Settings
from src.config.smtp import SMTPSettings


class TestLLMSettings:
    """Группа тестов настроек LLM-клиентов."""

    def test_rejects_non_positive_limits(self) -> None:
        """
        Тестируем: запрет неположительных лимитов запросов.
        Отдаём: llm_request_limit=0.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            LLMSettings(llm_request_limit=0)

    def test_rejects_non_positive_timeouts(self) -> None:
        """
        Тестируем: запрет неположительных таймаутов.
        Отдаём: hf_timeout_seconds=-1.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            LLMSettings(hf_timeout_seconds=-1)

    def test_provider_models_have_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию моделей.
        Отдаём: LLMSettings без аргументов.
        Ожидаем: заданы hf_model и hf_cards_model.
        """
        settings_model = LLMSettings()

        assert settings_model.hf_model
        assert settings_model.hf_cards_model


class TestOtherSettingsBlocks:
    """Группа тестов остальных блоков настроек."""

    def test_rag_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию RAG.
        Отдаём: RAGSettings без аргументов.
        Ожидаем: chunk больше overlap, top_k положительный.
        """
        settings_model = RAGSettings()

        assert settings_model.rag_chunk_size > settings_model.rag_chunk_overlap
        assert settings_model.rag_top_k >= 1

    def test_redis_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию Redis.
        Отдаём: RedisSettings без аргументов.
        Ожидаем: включён, не обязателен, URL по умолчанию задан.
        """
        settings_model = RedisSettings()

        assert settings_model.redis_enabled is True
        assert settings_model.redis_required is False
        assert settings_model.redis_url

    def test_smtp_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию SMTP.
        Отдаём: SMTPSettings без аргументов.
        Ожидаем: порт 587, TLS включён, адрес отправителя задан.
        """
        settings_model = SMTPSettings()

        assert settings_model.smtp_port == 587
        assert settings_model.smtp_use_tls is True
        assert settings_model.smtp_from

    def test_elasticsearch_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию Elasticsearch.
        Отдаём: ElasticsearchSettings без аргументов.
        Ожидаем: выключен по умолчанию, имя индекса задано.
        """
        settings_model = ElasticsearchSettings()

        assert settings_model.elasticsearch_enabled is False
        assert settings_model.elasticsearch_log_index == "immersjp-logs"


class TestSettingsComposition:
    """Группа тестов корневого объекта настроек."""

    def test_settings_singleton_has_all_blocks(self) -> None:
        """
        Тестируем: полноту сборки корневых настроек.
        Отдаём: синглтон settings из src.config.settings.
        Ожидаем: доступны все восемь блоков конфигурации.
        """
        from src.config.settings import settings as singleton

        assert isinstance(singleton, Settings)
        assert singleton.app and singleton.db and singleton.security
        assert singleton.llm and singleton.rag and singleton.redis
        assert singleton.smtp and singleton.elasticsearch
