from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.domain.user import LanguageLevel, LearningGoal, SkillAssessment, User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def mark_email_verified(self, user_id: int) -> User:
        pass

    @abstractmethod
    async def update_learning_profile(
        self,
        user_id: int,
        goal: LearningGoal,
        language_level: LanguageLevel,
        interests: list[str],
        skill_assessment: SkillAssessment,
    ) -> User:
        pass
