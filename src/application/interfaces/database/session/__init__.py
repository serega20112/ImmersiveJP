"""Порты репозитория учебных сессий."""

from .read import LearningSessionReadRepositoryPort
from .write import LearningSessionWriteRepositoryPort


class LearningSessionRepositoryPort(
    LearningSessionReadRepositoryPort,
    LearningSessionWriteRepositoryPort,
):
    """Комбинированный порт репозитория учебных сессий."""


__all__ = [
    "LearningSessionReadRepositoryPort",
    "LearningSessionRepositoryPort",
    "LearningSessionWriteRepositoryPort",
]
