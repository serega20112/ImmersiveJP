"""
Юнит-тесты перечислений профиля пользователя.

Проверяются: строковые значения уровней языка, целей обучения
и сроков изучения, а также поведение StrEnum-перечислений.
"""

import pytest

from src.domain.value_objects.user import LanguageLevel, LearningGoal, StudyTimeline


class TestLanguageLevel:
    """Группа тестов уровней владения языком."""

    @pytest.mark.parametrize(
        "member, value",
        [("ZERO", "zero"), ("BASIC", "basic"), ("INTERMEDIATE", "intermediate")],
        ids=str.lower,
    )
    def test_string_values(self, member: str, value: str) -> None:
        """
        Тестируем: строковые значения уровня языка.
        Отдаём: имя члена перечисления.
        Ожидаем: значение совпадает со строкой уровня.
        """
        assert LanguageLevel[member] == value

    def test_is_str_enum(self) -> None:
        """
        Тестируем: совместимость уровня с обычной строкой.
        Отдаём: член перечисления BASIC.
        Ожидаем: равенство строке "basic" без приведения.
        """
        assert LanguageLevel.BASIC == "basic"
        assert isinstance(LanguageLevel.BASIC, str)

    def test_unknown_value_raises(self) -> None:
        """
        Тестируем: валидацию неизвестного уровня.
        Отдаём: строку, которой нет в перечислении.
        Ожидаем: ValueError.
        """
        with pytest.raises(ValueError):
            LanguageLevel("advanced")


class TestLearningGoalAndTimeline:
    """Группа тестов целей обучения и сроков изучения."""

    @pytest.mark.parametrize(
        "member, value",
        [("TOURISM", "tourism"), ("RELOCATION", "relocation"), ("WORK", "work"), ("UNIVERSITY", "university")],
        ids=str.lower,
    )
    def test_learning_goal_values(self, member: str, value: str) -> None:
        """
        Тестируем: строковые значения цели обучения.
        Отдаём: имя члена перечисления.
        Ожидаем: значение совпадает с ожидаемой строкой.
        """
        assert LearningGoal[member] == value

    @pytest.mark.parametrize(
        "member, value",
        [
            ("THREE_MONTHS", "three_months"),
            ("SIX_MONTHS", "six_months"),
            ("ONE_YEAR", "one_year"),
            ("TWO_YEARS", "two_years"),
            ("FLEXIBLE", "flexible"),
        ],
        ids=str.lower,
    )
    def test_study_timeline_values(self, member: str, value: str) -> None:
        """
        Тестируем: строковые значения срока изучения.
        Отдаём: имя члена перечисления.
        Ожидаем: значение совпадает с ожидаемой строкой.
        """
        assert StudyTimeline[member] == value

    def test_members_are_distinct(self) -> None:
        """
        Тестируем: уникальность значений перечислений.
        Отдаём: полные наборы членов LearningGoal и StudyTimeline.
        Ожидаем: количество значений совпадает с количеством членов.
        """
        assert len(set(LearningGoal)) == len(LearningGoal)
        assert len(set(StudyTimeline)) == len(StudyTimeline)
