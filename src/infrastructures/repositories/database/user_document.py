"""SQLAlchemy-реализация репозитория пользовательских документов."""

from __future__ import annotations

from sqlalchemy import select

from src.application.interfaces.database import UserDocumentRepositoryPort
from src.domain.entities import UserDocument
from src.domain.value_objects import DocumentTitle, Timestamp, UserDocumentID, UserID
from src.infrastructures.database.models.user_document_model import (
    UserDocument as UserDocumentModel,
)


class UserDocumentRepository(UserDocumentRepositoryPort):
    """Репозиторий документов поверх PostgreSQL/SQLAlchemy."""

    def __init__(self, session) -> None:
        self._session = session

    async def create(self, user_id: int, title: DocumentTitle, content: str) -> UserDocument:
        doc = UserDocumentModel(user_id=user_id, title=title.value, content=content)
        self._session.add(doc)
        await self._session.flush()
        return self.to_entity(doc)

    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.user_id == user_id)
        )
        return [self.to_entity(model) for model in result.scalars().all()]

    async def get(self, doc_id: int) -> UserDocument | None:
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    async def delete(self, doc_id: int) -> None:
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    def to_entity(self, model: UserDocumentModel) -> UserDocument:
        return UserDocument(
            id=UserDocumentID(model.id),
            user_id=UserID(model.user_id),
            title=DocumentTitle(model.title),
            content=model.content,
            created_at=Timestamp(model.created_at),
        )
