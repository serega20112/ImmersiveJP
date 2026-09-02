"""Интерфейс репозитория пользовательских документов."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.documents import UserDocument


class AbstractUserDocumentRepository(ABC):
    """Контракт доступа к пользовательским документам."""

    @abstractmethod
    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Создать документ пользователя."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Вернуть все документы пользователя."""

    @abstractmethod
    async def get(self, doc_id: int) -> UserDocument | None:
        """Вернуть документ по идентификатору или ``None``."""

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору."""
