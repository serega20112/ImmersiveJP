"""Порт записи репозитория пользовательских документов."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import UserDocument


class UserDocumentWriteRepositoryPort(ABC):
    """Порт записи пользовательских документов."""

    @abstractmethod
    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Создать новый документ пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору."""
        raise NotImplementedError
