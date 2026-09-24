"""
Юнит-тесты агрегата User.

Проверяются переходы состояния: подтверждение email, завершение онбординга,
повторные (запрещённые) переходы и обновление отображаемого имени.
"""

import pytest

from src.domain.aggregates.user import User
from src.domain.exceptions import UserAlreadyVerifiedError, UserNotOnboardedError
from src.domain.value_objects import DisplayName, Email, PasswordHash
from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.user import LanguageLevel, LearningGoal, StudyTimeline
from tests.fixtures.factories.user_factory import UserFactory


class TestUserAggregate:
    """Группа тестов переходов состояния агрегата User."""

    def test_create_returns_unverified_user_with_timestamps(self) -> None:
        """
        Тестируем: фабричный метод create для нового пользователя.
        Отдаём: валидные email, хеш пароля и отображаемое имя.
        Ожидаем: пользователь создан без id, email не подтверждён, онбординг не пройден,
                 времена создания и обновления совпадают.
        """
        user = User.create(
            email=Email("new@example.com"),
            password_hash=PasswordHash("hashed"),
            display_name=DisplayName("Новый"),
        )

        assert user.id is None
        assert user.is_email_verified is False
        assert user.onboarding_completed is False
        assert user.created_at == user.updated_at

    def test_verify_email_sets_flag_and_raises_on_second_call(self, user_factory: UserFactory) -> None:
        """
        Тестируем: подтверждение email и повторное подтверждение.
        Отдаём: неподтверждённый пользователь; затем повторный вызов verify_email.
        Ожидаем: флаг становится True, повторный вызов выбрасывает UserAlreadyVerifiedError.
        """
        user = user_factory.build()

        user.verify_email()

        assert user.is_email_verified is True
        with pytest.raises(UserAlreadyVerifiedError):
            user.verify_email()

    def test_complete_onboarding_fills_profile(self, user_factory: UserFactory) -> None:
        """
        Тестируем: успешное завершение онбординга.
        Отдаём: пользователь без завершённого онбординга и валидные цель, уровень,
                срок, интересы и результат диагностики.
        Ожидаем: профиль заполнен, флаг onboarding_completed установлен.
        """
        user = user_factory.build()
        assessment = SkillAssessment(score=50, estimated_level=LanguageLevel.BASIC)

        user.complete_onboarding(
            goal=LearningGoal.TOURISM,
            level=LanguageLevel.BASIC,
            timeline=StudyTimeline.SIX_MONTHS,
            interests=["аниме", "путешествия"],
            assessment=assessment,
        )

        assert user.onboarding_completed is True
        assert user.learning_goal == LearningGoal.TOURISM
        assert user.language_level == LanguageLevel.BASIC
        assert user.study_timeline == StudyTimeline.SIX_MONTHS
        assert user.interests == ["аниме", "путешествия"]
        assert user.skill_assessment == assessment

    def test_complete_onboarding_raises_when_already_completed(self) -> None:
        """
        Тестируем: повторное завершение онбординга.
        Отдаём: пользователь с завершённым онбордингом.
        Ожидаем: выброс UserNotOnboardedError.
        """
        user = UserFactory(onboarding_completed=True).build()

        with pytest.raises(UserNotOnboardedError):
            user.complete_onboarding(
                goal=LearningGoal.TOURISM,
                level=LanguageLevel.BASIC,
                timeline=StudyTimeline.SIX_MONTHS,
                interests=["аниме"],
                assessment=SkillAssessment(),
            )

    def test_update_display_name_replaces_value(self, user_factory: UserFactory) -> None:
        """
        Тестируем: обновление отображаемого имени.
        Отдаём: пользователь и новое корректное имя.
        Ожидаем: display_name заменён, время обновления не раньше прежнего.
        """
        user = user_factory.build()
        previous_updated_at = user.updated_at

        user.update_display_name(DisplayName("Новое имя"))

        assert str(user.display_name) == "Новое имя"
        assert user.updated_at.value >= previous_updated_at.value

