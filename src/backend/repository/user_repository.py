from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.user import LanguageLevel, LearningGoal, User
from src.backend.infrastructure.models import UserModel
from src.backend.infrastructure.repositories import AbstractUserRepository


class UserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            display_name=user.display_name,
            is_email_verified=user.is_email_verified,
            learning_goal=user.learning_goal.value if user.learning_goal else None,
            language_level=user.language_level.value if user.language_level else None,
            interests_json=user.interests,
            onboarding_completed=user.onboarding_completed,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def mark_email_verified(self, user_id: int) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one()
        model.is_email_verified = True
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_learning_profile(
        self,
        user_id: int,
        goal: LearningGoal,
        language_level: LanguageLevel,
        interests: list[str],
    ) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one()
        model.learning_goal = goal.value
        model.language_level = language_level.value
        model.interests_json = interests
        model.onboarding_completed = True
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            display_name=model.display_name,
            is_email_verified=model.is_email_verified,
            learning_goal=(
                LearningGoal(model.learning_goal) if model.learning_goal else None
            ),
            language_level=(
                LanguageLevel(model.language_level) if model.language_level else None
            ),
            interests=list(model.interests_json or []),
            onboarding_completed=model.onboarding_completed,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
