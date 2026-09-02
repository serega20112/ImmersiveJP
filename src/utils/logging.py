"""Нейтральные помощники логирования, доступные всем слоям."""

from __future__ import annotations

import logging
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Вернуть именованный logger.

    Args:
        name: Имя логгера, обычно ``__name__`` модуля.

    Returns:
        Настроенный стандартный logger.
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    """Записать структурированное событие в лог.

    Args:
        logger: Целевой логгер.
        level: Уровень записи (например, ``logging.INFO``).
        event: Машиночитаемый код события.
        message: Человекочитаемое описание.
        **fields: Дополнительные структурированные поля события.
    """
    logger.log(level, message, extra={"event": event, "extra_fields": fields})
