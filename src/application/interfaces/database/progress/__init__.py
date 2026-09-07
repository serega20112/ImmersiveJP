"""Порты репозитория прогресса."""

from .read import ProgressReadRepositoryPort
from .write import ProgressWriteRepositoryPort


class ProgressRepositoryPort(ProgressReadRepositoryPort, ProgressWriteRepositoryPort):
    """Комбинированный порт репозитория прогресса."""


__all__ = [
    "ProgressReadRepositoryPort",
    "ProgressRepositoryPort",
    "ProgressWriteRepositoryPort",
]
