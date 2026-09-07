from __future__ import annotations

from pydantic import BaseModel, model_validator

from .app import AppSettings
from .database import DatabaseSettings
from .elasticsearch import ElasticsearchSettings
from .llm import LLMSettings
from .rag import RAGSettings
from .redis import RedisSettings
from .security import SecuritySettings
from .smtp import SMTPSettings

_PLACEHOLDER_SECRETS = {
    "change-me",
    "change-me-too",
    "immersjp-secret-key",
    "immersjp-session-secret",
}


class Settings(BaseModel):
    """Корневые настройки приложения."""

    app: AppSettings
    db: DatabaseSettings
    security: SecuritySettings
    llm: LLMSettings
    rag: RAGSettings
    redis: RedisSettings
    smtp: SMTPSettings
    elasticsearch: ElasticsearchSettings

    @classmethod
    def load(cls) -> Settings:
        """
        Единая точка сборки настроек.

        Каждый блок сам читает env/.env.
        """
        return cls(
            app=AppSettings(),
            db=DatabaseSettings(),
            security=SecuritySettings(),
            llm=LLMSettings(),
            rag=RAGSettings(),
            redis=RedisSettings(),
            smtp=SMTPSettings(),
            elasticsearch=ElasticsearchSettings(),
        )

    @model_validator(mode="after")
    def validate_secret_strength(self) -> Settings:
        if not self.app.app_debug:
            for attr in ("secret_key", "session_secret"):
                secret = getattr(self.security, attr)
                if len(secret) < 16 or secret in _PLACEHOLDER_SECRETS:
                    raise ValueError(
                        f"{attr} is too weak for non-debug mode. "
                        "Set a non-placeholder value with at least 16 characters."
                    )
        return self


def get_settings() -> Settings:
    """
    Вернуть синглтон настроек приложения.

    Нужен для кэширования дорогого чтения env/.env при старте.
    """
    if not hasattr(get_settings, "_settings"):
        get_settings._settings = Settings.load()
    return get_settings._settings


settings = get_settings()
