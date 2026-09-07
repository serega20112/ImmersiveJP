"""Схемы системных эндпоинтов."""

from __future__ import annotations

from pydantic import BaseModel


class SystemHealthResponse(BaseModel):
    """Ответ проверки работоспособности приложения.

    Атрибуты:
        status: Статус системы.
        app: Название приложения.
        metrics_enabled: Флаг включённого сбора метрик.
        rate_limit_enabled: Флаг включённого ограничения частоты запросов.
    """

    status: str
    app: str
    metrics_enabled: bool
    rate_limit_enabled: bool
