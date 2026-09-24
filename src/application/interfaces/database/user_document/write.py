"""Порт записи репозитория пользовательских документов."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import UserDocument
from src.domain.value_objects import DocumentTitle


class UserDocumentWriteRepositoryPort(ABC):
    """Порт записи пользовательских документов."""

    @abstractmethod
    async def create(self, user_id: int, title: DocumentTitle, content: str) -> UserDocument:
        """Создать новый документ пользователя.

        Заголовок принимается value object'ом, а не строкой: инвариант
        «не пустой» обязан быть выполнен до обращения к базе. Иначе запись
        уходит в БД, а прочитать её назад невозможно — разбор строки в
        DocumentTitle бросает исключение уже на чтении.

        Args:
            user_id: Идентификатор владельца.
            title: Проверенный заголовок.
            content: Текст документа.

        Returns:
            Созданный документ.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору."""
        raise NotImplementedError
