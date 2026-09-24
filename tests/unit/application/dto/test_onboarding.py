"""
Юнит-тесты DTO онбординга.

Проверяются: значения по умолчанию формы, вложенность диагностических
вопросов и обязательность оценки навыков в результате онбординга.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.onboarding import (
    DiagnosticOptionDTO,
    DiagnosticQuestionDTO,
    DiagnosticQuestionGroupDTO,
    OnboardingDTO,
    OnboardingPageDTO,
    OnboardingResultDTO,
    StudyTimelineOptionDTO,
)
from src.application.dto.skill import SkillAssessmentDTO


class TestDiagnosticDTOs:
    """Группа тестов DTO диагностических вопросов."""

    def test_question_defaults_hints_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию подсказок вопроса.
        Отдаём: вопрос без подсказок.
        Ожидаем: hints — пустой список.
        """
        dto = DiagnosticQuestionDTO(
            key="q1",
            prompt="Вопрос",
            skill_label="Лексика",
            options=[DiagnosticOptionDTO(value="a", label="A", description="desc")],
        )

        assert dto.hints == []

    def test_group_defaults_questions_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию списка вопросов группы.
        Отдаём: группу без вопросов.
        Ожидаем: questions — пустой список.
        """
        group = DiagnosticQuestionGroupDTO(level="n5", title="N5", description="Базовый")

        assert group.questions == []


class TestOnboardingPageDTO:
    """Группа тестов DTO страницы онбординга."""

    def test_defaults_lists_to_empty(self) -> None:
        """
        Тестируем: значения по умолчанию списков страницы.
        Отдаём: пустую страницу онбординга.
        Ожидаем: группы диагностики и варианты срока — пустые списки.
        """
        page = OnboardingPageDTO()

        assert page.diagnostic_groups == []
        assert page.study_timeline_options == []

    def test_timeline_option_keeps_fields(self) -> None:
        """
        Тестируем: DTO варианта срока обучения.
        Отдаём: вариант срока с полями.
        Ожидаем: значения сохранены.
        """
        option = StudyTimelineOptionDTO(value="3m", title="3 месяца", description="Спринт")

        assert option.value == "3m"


class TestOnboardingDTO:
    """Группа тестов DTO формы онбординга."""

    def test_defaults_for_answers_and_hints(self) -> None:
        """
        Тестируем: значения по умолчанию ответов и счётчика подсказок.
        Отдаём: только обязательные текстовые поля формы.
        Ожидаем: ответы — пустой словарь, число подсказок — 0.
        """
        dto = OnboardingDTO(
            goal="Работа",
            language_level="n5",
            study_timeline="3m",
            interests_text="аниме, музыка",
        )

        assert dto.diagnostic_answers == {}
        assert dto.diagnostic_hints_used == 0


class TestOnboardingResultDTO:
    """Группа тестов DTO результата завершения онбординга."""

    def test_requires_skill_assessment(self) -> None:
        """
        Тестируем: обязательность оценки навыков в результате.
        Отдаём: результат без skill_assessment.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            OnboardingResultDTO(user_id=1, generated_batches={"jlpt": 1})

    def test_keeps_generated_batches(self) -> None:
        """
        Тестируем: сохранение числа созданных партий по трекам.
        Отдаём: карту треков и оценку навыков.
        Ожидаем: данные доступны без изменений.
        """
        assessment = SkillAssessmentDTO(score=10, summary="Базовый")

        dto = OnboardingResultDTO(user_id=1, generated_batches={"jlpt": 2}, skill_assessment=assessment)

        assert dto.generated_batches == {"jlpt": 2}
        assert dto.skill_assessment.score == 10
