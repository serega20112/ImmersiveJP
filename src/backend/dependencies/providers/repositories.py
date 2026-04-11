from __future__ import annotations

from functools import cached_property

from src.backend.repository import (
    ContentRepository,
    MentorRepository,
    ProgressRepository,
    SessionRepository,
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
