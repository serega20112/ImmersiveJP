"""Общие утилиты, не зависящие от слоёв приложения."""

from .logging import get_logger, log_event

__all__ = ["get_logger", "log_event"]
