from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from src.domain.exceptions import (
    UserAlreadyVerifiedError,
    UserNotOnboardedError,
)
from src.domain.value_objects import (
    DisplayName,
    Email,
    LanguageLevel,
    LearningGoal,
    PasswordHash,
    SkillAssessment,
    StudyTimeline,
    Timestamp,
    UserID,
)


@dataclass
class User:
    """Доменная модель пользователя."""

    email: Email
    password_hash: PasswordHash
    display_name: DisplayName
    created_at: Timestamp
    updated_at: Timestamp
    id: UserID | None = None
    is_email_verified: bool = False
    learning_goal: LearningGoal | None = None
    language_level: LanguageLevel | None = None
    study_timeline: StudyTimeline | None = None
    interests: list[str] = field(default_factory=list)
    onboarding_completed: bool = False
    skill_assessment: SkillAssessment | None = None

    @classmethod
    def create(
        cls,
        email: Email,
        password_hash: PasswordHash,
        display_name: DisplayName,
    ) -> Self:
        """Создаёт нового пользователя с неподтверждённым email.

        Args:
            email: Электронная почта пользователя.
            password_hash: Хеш пароля.
            display_name: Отображаемое имя.

        Returns:
            Новый пользователь. ID назначается при сохранении в БД.
        """
        timestamp = Timestamp.now()
        return cls(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def verify_email(self) -> None:
        """Подтверждает email пользователя.

        Raises:
            UserAlreadyVerifiedError: Email уже подтверждён.
        """
        if self.is_email_verified:
            raise UserAlreadyVerifiedError(
                f"Email {self.email} уже подтверждён",
                details={"email": str(self.email)},
            )
        self.is_email_verified = True
        self.updated_at = self.updated_at.refresh()

    def complete_onboarding(
        self,
        goal: LearningGoal,
        level: LanguageLevel,
        timeline: StudyTimeline,
        interests: list[str],
        assessment: SkillAssessment,
    ) -> None:
        """Завершает онбординг, заполняя профиль обучения.

        Args:
            goal: Цель обучения.
            level: Уровень языка.
            timeline: Срок обучения.
            interests: Интересы пользователя.
            assessment: Результат диагностики.
        """
        if self.onboarding_completed:
            raise UserNotOnboardedError("Онбординг уже завершён")
        self.learning_goal = goal
        self.language_level = level
        self.study_timeline = timeline
        self.interests = list(interests)
        self.skill_assessment = assessment
        self.onboarding_completed = True
        self.updated_at = self.updated_at.refresh()

    def change_password(self, new_password_hash: PasswordHash) -> None:
        """Сменить пароль пользователя.

        Args:
            new_password_hash: Хеш нового пароля.
        """
        self.password_hash = new_password_hash
        self.updated_at = self.updated_at.refresh()

    def update_display_name(self, new_name: DisplayName) -> None:
        """Обновить отображаемое имя.

        Args:
            new_name: Новое отображаемое имя.
        """
        self.display_name = new_name
        self.updated_at = self.updated_at.refresh()
