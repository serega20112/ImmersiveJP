from src.infrastructures.repositories.base_clients import SQLAlchemyUnitOfWork

from .content import LearningCardRepository
from .course import CourseRepository
from .progress import ProgressRepository
from .session import SessionRepository
from .skill_area import SkillAreaRepository
from .user import UserRepository
from .user_document import UserDocumentRepository


class ImmersiveUnitOfWork(SQLAlchemyUnitOfWork):
    """Единый Unit of Work для всех SQLAlchemy-репозиториев приложения."""

    def _register_repositories(self) -> None:
        """Зарегистрировать все SQLAlchemy-репозитории на одной сессии."""
        self._repositories["user"] = UserRepository(self._session)
        self._repositories["content"] = LearningCardRepository(self._session)
        self._repositories["course"] = CourseRepository(self._session)
        self._repositories["progress"] = ProgressRepository(self._session)
        self._repositories["session"] = SessionRepository(self._session)
        self._repositories["skill_area"] = SkillAreaRepository(self._session)
        self._repositories["user_document"] = UserDocumentRepository(self._session)
