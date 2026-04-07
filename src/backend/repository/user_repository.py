from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.user import (
    LanguageLevel,
    LearningGoal,
    SkillAssessment,
    StudyTimeline,
    User,
)
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
            study_timeline=user.study_timeline.value if user.study_timeline else None,
            interests_json=user.interests,
            onboarding_completed=user.onboarding_completed,
            diagnostic_score=(
                user.skill_assessment.score if user.skill_assessment is not None else None
            ),
            diagnostic_level=(
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            diagnostic_summary=(
                user.skill_assessment.summary if user.skill_assessment is not None else None
            ),
            strengths_json=(
                list(user.skill_assessment.strengths)
                if user.skill_assessment is not None
                else None
            ),
            weak_points_json=(
                list(user.skill_assessment.weak_points)
                if user.skill_assessment is not None
                else None
            ),
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
        study_timeline: StudyTimeline,
        interests: list[str],
        skill_assessment: SkillAssessment,
    ) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one()
        model.learning_goal = goal.value
        model.language_level = language_level.value
        model.study_timeline = study_timeline.value
        model.interests_json = interests
        model.onboarding_completed = True
        model.diagnostic_score = skill_assessment.score
        model.diagnostic_level = (
            skill_assessment.estimated_level.value
            if skill_assessment.estimated_level is not None
            else None
        )
        model.diagnostic_summary = skill_assessment.summary
        model.strengths_json = list(skill_assessment.strengths)
        model.weak_points_json = list(skill_assessment.weak_points)
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
            study_timeline=(
                StudyTimeline(model.study_timeline) if model.study_timeline else None
            ),
            interests=list(model.interests_json or []),
            onboarding_completed=model.onboarding_completed,
            skill_assessment=_to_skill_assessment(model),
            created_at=model.created_at,
            updated_at=model.updated_at,
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
        estimated_level=(
            LanguageLevel(model.diagnostic_level) if model.diagnostic_level else None
        ),
        summary=model.diagnostic_summary or "",
        strengths=list(model.strengths_json or []),
        weak_points=list(model.weak_points_json or []),
    )
