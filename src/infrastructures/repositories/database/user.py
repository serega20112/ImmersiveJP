from __future__ import annotations

from sqlalchemy import select

from src.application.interfaces.database import UserRepositoryPort
from src.domain.aggregates import User
from src.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    Timestamp,
    UserID,
)
from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.user import LanguageLevel, LearningGoal, StudyTimeline
from src.infrastructures.database.models import UserModel
from src.infrastructures.repositories.database.base import SQLAlchemyFullRepository
from src.utils import value_or_none


class UserRepository(UserRepositoryPort, SQLAlchemyFullRepository[User, UserID, object, UserModel]):
    """Репозиторий для CRUD-операций с пользователями."""

    model = UserModel

    async def add(self, user: User) -> User:
        """Сохранить нового пользователя в базу."""
        model = self.to_model(user)
        self._session.add(model)
        await self._session.flush()
        return self.to_entity(model)

    async def save(self, user: User) -> User:
        """Обновить существующего пользователя целиком."""
        if user.id is None:
            raise ValueError("Нельзя сохранить пользователя без ID")
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == int(user.id))
        )
        model = result.scalar_one()
        model.email = user.email.value
        model.password_hash = user.password_hash.value
        model.display_name = user.display_name.value
        model.is_email_verified = user.is_email_verified
        model.learning_goal = user.learning_goal.value if user.learning_goal else None
        model.language_level = user.language_level.value if user.language_level else None
        model.study_timeline = user.study_timeline.value if user.study_timeline else None
        model.interests_json = list(user.interests)
        model.onboarding_completed = user.onboarding_completed
        model.diagnostic_score = user.skill_assessment.score if user.skill_assessment else None
        model.diagnostic_level = (
            user.skill_assessment.estimated_level.value
            if user.skill_assessment and user.skill_assessment.estimated_level
            else None
        )
        model.diagnostic_summary = (
            user.skill_assessment.summary if user.skill_assessment else None
        )
        model.strengths_json = (
            list(user.skill_assessment.strengths) if user.skill_assessment else None
        )
        model.weak_points_json = (
            list(user.skill_assessment.weak_points) if user.skill_assessment else None
        )
        model.updated_at = user.updated_at.value
        await self._session.flush()
        return self.to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    def to_entity(self, model: UserModel) -> User:
        return User(
            id=UserID(model.id),
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash),
            display_name=DisplayName(model.display_name),
            is_email_verified=model.is_email_verified,
            learning_goal=(LearningGoal(model.learning_goal) if model.learning_goal else None),
            language_level=(LanguageLevel(model.language_level) if model.language_level else None),
            study_timeline=(StudyTimeline(model.study_timeline) if model.study_timeline else None),
            interests=list(model.interests_json or []),
            onboarding_completed=model.onboarding_completed,
            skill_assessment=_to_skill_assessment(model),
            created_at=Timestamp(model.created_at),
            updated_at=Timestamp(model.updated_at),
        )

    def to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=value_or_none(entity.id),
            email=value_or_none(entity.email),
            password_hash=value_or_none(entity.password_hash),
            display_name=value_or_none(entity.display_name),
            is_email_verified=entity.is_email_verified,
            learning_goal=entity.learning_goal.value if entity.learning_goal else None,
            language_level=entity.language_level.value if entity.language_level else None,
            study_timeline=entity.study_timeline.value if entity.study_timeline else None,
            interests_json=entity.interests,
            onboarding_completed=entity.onboarding_completed,
            diagnostic_score=entity.skill_assessment.score if entity.skill_assessment else None,
            diagnostic_level=(
                entity.skill_assessment.estimated_level.value
                if entity.skill_assessment and entity.skill_assessment.estimated_level
                else None
            ),
            diagnostic_summary=entity.skill_assessment.summary if entity.skill_assessment else None,
            strengths_json=list(entity.skill_assessment.strengths) if entity.skill_assessment else None,
            weak_points_json=(
                list(entity.skill_assessment.weak_points) if entity.skill_assessment else None
            ),
            created_at=value_or_none(entity.created_at),
            updated_at=value_or_none(entity.updated_at),
        )


def _to_skill_assessment(model: UserModel) -> SkillAssessment | None:
    if (
        model.diagnostic_score is None
        and model.diagnostic_level is None
        and not model.diagnostic_summary
        and not model.strengths_json
        and not model.weak_points_json
    ):
        return None
    return SkillAssessment(
        score=int(model.diagnostic_score or 0),
        estimated_level=(LanguageLevel(model.diagnostic_level) if model.diagnostic_level else None),
        summary=model.diagnostic_summary or "",
        strengths=list(model.strengths_json or []),
        weak_points=list(model.weak_points_json or []),
    )
