"""Общие фейки для unit-тестов без БД и внешних сервисов."""

from __future__ import annotations

from typing import Any

from src.domain.aggregates.user import User
from src.domain.entities.content import LearningCard
from src.domain.value_objects import (
    DisplayName,
    Email,
    LanguageLevel,
    LearningGoal,
    PasswordHash,
    SkillAssessment,
    StudyTimeline,
    Timestamp,
    TrackType,
    UserID,
)


class FakeUnitOfWork:
    """Минимальная реализация UnitOfWork для изолированных use case-тестов."""

    def __init__(self, repositories: dict[str, Any] | None = None) -> None:
        self._repositories = dict(repositories or {})

    async def __aenter__(self) -> FakeUnitOfWork:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    def repository(self, name: str) -> Any:
        if name not in self._repositories:
            raise KeyError(f"Repository {name!r} is not registered in FakeUnitOfWork")
        return self._repositories[name]

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def build_test_user(
    *,
    user_id: int = 1,
    email: str = "user@example.com",
    display_name: str = "Immers User",
    learning_goal: LearningGoal = LearningGoal.TOURISM,
    language_level: LanguageLevel = LanguageLevel.BASIC,
    study_timeline: StudyTimeline = StudyTimeline.SIX_MONTHS,
    interests: list[str] | None = None,
    onboarding_completed: bool = True,
    skill_assessment: SkillAssessment | None = None,
) -> User:
    """Собрать доменного пользователя с валидными value objects."""
    timestamp = Timestamp.now()
    return User(
        id=UserID(user_id),
        email=Email(email),
        password_hash=PasswordHash("$2b$12$testhashedpasswordvalue000000000000000000"),
        display_name=DisplayName(display_name),
        created_at=timestamp,
        updated_at=timestamp,
        is_email_verified=True,
        learning_goal=learning_goal,
        language_level=language_level,
        study_timeline=study_timeline,
        interests=list(interests or ["еда", "поездки"]),
        onboarding_completed=onboarding_completed,
        skill_assessment=skill_assessment,
    )


def build_test_card(
    *,
    card_id: int = 1,
    user_id: int = 1,
    track: TrackType = TrackType.LANGUAGE,
    topic: str = "Тема",
    explanation: str = "Объяснение",
    examples: list[str] | None = None,
    key_terms: list[str] | None = None,
    batch_number: int = 1,
    position: int = 1,
) -> LearningCard:
    """Собрать учебную карточку с валидными value objects."""
    return LearningCard.create(
        user_id=user_id,
        track=track,
        topic=topic,
        explanation=explanation,
        examples=list(examples or ["例文です。"]),
        key_terms=list(key_terms or ["例"]),
        batch_number=batch_number,
        position=position,
        card_id=card_id,
    )
