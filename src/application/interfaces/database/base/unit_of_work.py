"""Порт Unit of Work для управления транзакционной границей."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.application.interfaces.database.content import LearningCardRepositoryPort
    from src.application.interfaces.database.course import CourseRepositoryPort
    from src.application.interfaces.database.progress import ProgressRepositoryPort
    from src.application.interfaces.database.session import LearningSessionRepositoryPort
    from src.application.interfaces.database.skill_area import SkillAreaRepositoryPort
    from src.application.interfaces.database.user import UserRepositoryPort
    from src.application.interfaces.database.user_document import UserDocumentRepositoryPort


class UnitOfWork(ABC):
    """Порт Unit of Work для управления транзакционной границей.

    Репозитории доступны по именам через ``repository``, но обращаться к ним
    следует типизированными свойствами этого класса. Причина не в стиле:
    ``repository`` возвращает ``Any``, и в этой единственной точке проекта
    вся аккуратная типизация DTO и value objects исчезает. Опечатка в строке
    ``"user_documnet"`` не ловится ни линтером, ни mypy, а IDE не подсказывает,
    какие методы у репозитория есть. Свойства собирают имена ключей в одном
    месте, поэтому новое имя репозитория встречается один раз, а не в десятках
    юзкейсов.

    Наследники обязаны реализовать ``repository``; свойства наследуются готовые,
    что держит тестовые подмены работоспособными.
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    def repository(self, name: str) -> Any:
        """Получить репозиторий по имени.

        Низовой механизм: у тестовых подмен он единственный. В прикладном коде
        предпочтительны свойства ниже, где тип известен.

        Args:
            name: Имя репозитория.

        Returns:
            Реализация репозитория.
        """
        pass

    @property
    def users(self) -> UserRepositoryPort:
        """Репозиторий пользователей."""
        return self.repository("user")

    @property
    def learning_cards(self) -> LearningCardRepositoryPort:
        """Репозиторий учебных карточек."""
        return self.repository("content")

    @property
    def sessions(self) -> LearningSessionRepositoryPort:
        """Репозиторий учебных сессий."""
        return self.repository("session")

    @property
    def progress(self) -> ProgressRepositoryPort:
        """Репозиторий прогресса."""
        return self.repository("progress")

    @property
    def course(self) -> CourseRepositoryPort:
        """Репозиторий программы обучения."""
        return self.repository("course")

    @property
    def skill_areas(self) -> SkillAreaRepositoryPort:
        """Репозиторий областей навыков."""
        return self.repository("skill_area")

    @property
    def user_documents(self) -> UserDocumentRepositoryPort:
        """Репозиторий пользовательских документов."""
        return self.repository("user_document")
