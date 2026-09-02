from __future__ import annotations

from functools import cached_property

from src.application.services.rag_service import RAGService
from src.infrastructures.repositories.implementations import (
    ContentRepository,
    MentorRepository,
    ProgressRepository,
    SessionRepository,
    UserDocumentRepository,
    UserRepository,
)


class RepositoryProvidersMixin:
    @cached_property
    def user_repository(self) -> UserRepository:
        return UserRepository(self.session)

    @cached_property
    def content_repository(self) -> ContentRepository:
        return ContentRepository(self.session)

    @cached_property
    def progress_repository(self) -> ProgressRepository:
        return ProgressRepository(self.session)

    @cached_property
    def mentor_repository(self) -> MentorRepository:
        return MentorRepository(self.root.key_value_store)

    @cached_property
    def session_repository(self) -> SessionRepository:
        return SessionRepository(self.session)

    @cached_property
    def user_document_repository(self) -> UserDocumentRepository:
        return UserDocumentRepository(self.session)

    @cached_property
    def rag_service(self) -> RAGService:
        return RAGService(
            self.user_document_repository,
            self.root.embedding_client,
            cache=self.root.key_value_store,
        )
