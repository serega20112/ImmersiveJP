"""Порты репозитория пользовательских документов."""

from .read import UserDocumentReadRepositoryPort
from .write import UserDocumentWriteRepositoryPort


class UserDocumentRepositoryPort(UserDocumentReadRepositoryPort, UserDocumentWriteRepositoryPort):
    """Комбинированный порт репозитория пользовательских документов."""


__all__ = [
    "UserDocumentReadRepositoryPort",
    "UserDocumentRepositoryPort",
    "UserDocumentWriteRepositoryPort",
]
