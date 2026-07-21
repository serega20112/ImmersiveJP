from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.infrastructure.models.user_document_model import UserDocument


class AbstractUserDocumentRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        pass

    @abstractmethod
    async def get(self, doc_id: int) -> UserDocument | None:
        pass

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        pass
