"""Порты репозитория учебных карточек."""

from .read import LearningCardReadRepositoryPort
from .write import LearningCardWriteRepositoryPort


class LearningCardRepositoryPort(
    LearningCardReadRepositoryPort,
    LearningCardWriteRepositoryPort,
):
    """Комбинированный порт репозитория учебных карточек."""


__all__ = [
    "LearningCardReadRepositoryPort",
    "LearningCardRepositoryPort",
    "LearningCardWriteRepositoryPort",
]
