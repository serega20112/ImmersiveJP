"""Порты репозитория наставника."""

from .read import MentorReadRepositoryPort
from .write import MentorWriteRepositoryPort


class MentorRepositoryPort(MentorReadRepositoryPort, MentorWriteRepositoryPort):
    """Комбинированный порт репозитория наставника."""


__all__ = [
    "MentorReadRepositoryPort",
    "MentorRepositoryPort",
    "MentorWriteRepositoryPort",
]
