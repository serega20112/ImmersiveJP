from __future__ import annotations

from functools import cached_property

from src.application.services import DocumentService, RAGService
from src.infrastructures.database import get_session_factory
from src.infrastructures.external.cached_embedding_client import CachedEmbeddingClient
from src.infrastructures.repositories.database import (
    ImmersiveUnitOfWork,
    MentorRepository,
)


class RepositoryProvidersMixin:
    @cached_property
    def uow(self) -> ImmersiveUnitOfWork:
        return ImmersiveUnitOfWork(get_session_factory())

    @cached_property
    def mentor_repository(self) -> MentorRepository:
        return MentorRepository(self.root.key_value_store)

    @cached_property
    def document_service(self) -> DocumentService:
        return DocumentService(self.uow)

    @cached_property
    def rag_service(self) -> RAGService:
        return RAGService(
            lambda: ImmersiveUnitOfWork(get_session_factory()),
            CachedEmbeddingClient(
                self.root.embedding_client,
                self.root.key_value_store,
            ),
        )
