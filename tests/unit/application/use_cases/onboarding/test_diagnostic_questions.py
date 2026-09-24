"""Юнит-тесты конструктора диагностических вопросов онбординга."""

import pytest

from src.application.use_cases.onboarding.diagnostic_questions import (
    _DIAGNOSTIC_BANKS,
    build_onboarding_question_groups,
    build_study_timeline_options,
    evaluate_diagnostic_answers,
)
from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.user import LanguageLevel, StudyTimeline


def _correct_answers(level: LanguageLevel) -> dict[str, str]:
    """Правильные ответы банка указанного уровня (белый ящик по банку).

    Args:
        level: Уровень языка.

    Returns:
        Словарь ключ вопроса -> корректное значение.
    """
    return {item["key"]: item["correct"] for item in _DIAGNOSTIC_BANKS[level]["questions"]}


class TestBuildOnboardingQuestionGroups:
    """Группа тестов сборки групп диагностических вопросов."""

    def test_covers_all_levels_with_five_questions(self) -> None:
        """
        Тестируем: полноту банков вопросов.
        Отдаём: вызов конструктора групп.
        Ожидаем: группа на каждый LanguageLevel, по 5 вопросов с вариантами и подсказками.
        """
        groups = build_onboarding_question_groups()

        assert [group.level for group in groups] == [level.value for level in LanguageLevel]
        for group in groups:
            assert group.title
            assert len(group.questions) == 5
            assert all(question.options for question in group.questions)

    def test_timeline_options_cover_all_values(self) -> None:
        """
        Тестируем: набор вариантов срока обучения.
        Отдаём: вызов конструктора опций.
        Ожидаем: по одной опции на каждое значение StudyTimeline.
        """
        options = build_study_timeline_options()

        assert [option.value for option in options] == [item.value for item in StudyTimeline]


class TestEvaluateDiagnosticAnswers:
    """Группа тестов вычисления результата диагностики."""

    def test_all_correct_gives_max_score(self) -> None:
        """
        Тестируем: диагностику со всеми верными ответами.
        Отдаём: правильные ответы уровня basic, без подсказок.
        Ожидаем: score=5, список сильных сторон не пуст, слабых нет.
        """
        assessment = evaluate_diagnostic_answers(_correct_answers(LanguageLevel.BASIC), LanguageLevel.BASIC)

        assert isinstance(assessment, SkillAssessment)
        assert assessment.score == 5
        assert assessment.strengths
        assert assessment.weak_points == []
        assert assessment.summary

    def test_missing_answers_raise_value_error(self) -> None:
        """
        Тестируем: неполный набор ответов.
        Отдаём: словарь без одного вопроса.
        Ожидаем: ValueError с требованием ответить на все вопросы.
        """
        answers = _correct_answers(LanguageLevel.ZERO)
        answers.pop(next(iter(answers)))

        with pytest.raises(ValueError):
            evaluate_diagnostic_answers(answers, LanguageLevel.ZERO)

    def test_hints_reduce_score(self) -> None:
        """
        Тестируем: штраф за подсказки.
        Отдаём: верные ответы уровня zero и hints_used=6 (штраф 2).
        Ожидаем: score=3 (5 минус 2).
        """
        assessment = evaluate_diagnostic_answers(_correct_answers(LanguageLevel.ZERO), LanguageLevel.ZERO, hints_used=6)

        assert assessment.score == 3

    def test_low_score_keeps_zero_level(self) -> None:
        """
        Тестируем: низкий результат на объявленном zero.
        Отдаём: все неверные ответы уровня zero.
        Ожидаем: estimated_level=zero.
        """
        wrong = dict.fromkeys(_correct_answers(LanguageLevel.ZERO), "definitely-wrong")

        assessment = evaluate_diagnostic_answers(wrong, LanguageLevel.ZERO)

        assert assessment.estimated_level == LanguageLevel.ZERO
        assert assessment.score == 0
        assert assessment.weak_points
