"""Порт чтения репозитория пользовательских документов."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import UserDocument


class UserDocumentReadRepositoryPort(ABC):
    """Порт чтения пользовательских документов."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Получить все документы пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, doc_id: int) -> UserDocument | None:
        """Получить документ по идентификатору."""
        raise NotImplementedError
