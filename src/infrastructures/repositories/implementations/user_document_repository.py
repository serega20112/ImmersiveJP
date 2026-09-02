"""SQLAlchemy-реализация репозитория пользовательских документов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.abstract_user_document_repository import (
    AbstractUserDocumentRepository,
)
from src.domain.documents import UserDocument
from src.infrastructures.database.models.user_document_model import (
    UserDocument as UserDocumentModel,
)


class UserDocumentRepository(AbstractUserDocumentRepository):
    """Репозиторий документов поверх PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Создать новый документ пользователя.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок документа.
            content: Текстовое содержимое документа.

        Returns:
            Созданная доменная сущность документа.
        """
        doc = UserDocumentModel(user_id=user_id, title=title, content=content)
        self._session.add(doc)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(doc)
        return self._to_entity(doc)

    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Получить все документы пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Список доменных сущностей документов.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.user_id == user_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get(self, doc_id: int) -> UserDocument | None:
        """Получить документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.

        Returns:
            Доменная сущность документа или ``None``.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: UserDocumentModel) -> UserDocument:
        """Преобразовать ORM-модель в доменную сущность."""
        return UserDocument(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
        )
