from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.models.user_document_model import UserDocument
from src.backend.infrastructure.repositories.abstract_user_document_repository import (
    AbstractUserDocumentRepository,
)


class UserDocumentRepository(AbstractUserDocumentRepository):
    def __init__(self, session: AsyncSession):
        """Initialize the user document repository.

        Args:
            session: The async database session.
        """
        self._session = session

    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Create a new user document.

        Args:
            user_id: ID of the user.
            title: Title of the document.
            content: Content of the document.

        Returns:
            The created user document.
        """
        doc = UserDocument(user_id=user_id, title=title, content=content)
        self._session.add(doc)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Get all documents for a user.

        Args:
            user_id: ID of the user.

        Returns:
            A list of user documents.
        """
        result = await self._session.execute(
            select(UserDocument).where(UserDocument.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get(self, doc_id: int) -> UserDocument | None:
        """Get a document by its ID.

        Args:
            doc_id: ID of the document.

        Returns:
            The user document, or None if not found.
        """
        result = await self._session.execute(select(UserDocument).where(UserDocument.id == doc_id))
        return result.scalar_one_or_none()

    async def delete(self, doc_id: int) -> None:
        """Delete a document by its ID.

        Args:
            doc_id: ID of the document to delete.
        """
        doc = await self.get(doc_id)
        if doc is not None:
            await self._session.delete(doc)
            await self._session.commit()
