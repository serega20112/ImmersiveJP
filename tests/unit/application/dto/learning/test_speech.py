"""
Юнит-тесты DTO речевой практики.

Проверяются: значения по умолчанию фраз, реплик и упражнений,
а также структура страницы речевой практики.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.learning.speech import (
    SpeechDialogueDTO,
    SpeechDialogueTurnDTO,
    SpeechLineDTO,
    SpeechPracticeDTO,
    SpeechPracticePageDTO,
)


class TestSpeechLineDTO:
    """Группа тестов DTO одной фразы речевой практики."""

    def test_optional_parts_default_to_none(self) -> None:
        """
        Тестируем: значения по умолчанию транслитерации и перевода.
        Отдаём: фразу только на японском.
        Ожидаем: romaji и translation равны None.
        """
        line = SpeechLineDTO(japanese="こんにちは")

        assert line.romaji is None
        assert line.translation is None


class TestSpeechDialogueDTO:
    """Группа тестов DTO диалога речевой практики."""

    def test_turns_default_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию списка реплик.
        Отдаём: диалог без реплик.
        Ожидаем: turns — пустой список.
        """
        assert SpeechDialogueDTO(title="Кафе", scenario="Заказ").turns == []

    def test_keeps_turns(self) -> None:
        """
        Тестируем: сохранение реплик диалога.
        Отдаём: диалог с одной репликой.
        Ожидаем: реплика доступна с полем speaker.
        """
        turn = SpeechDialogueTurnDTO(speaker="Гость", japanese="お願いします")

        dialogue = SpeechDialogueDTO(title="Кафе", scenario="Заказ", turns=[turn])

        assert dialogue.turns[0].speaker == "Гость"


class TestSpeechPracticeDTO:
    """Группа тестов DTO набора упражнений."""

    def test_requires_tip_and_difficulty(self) -> None:
        """
        Тестируем: обязательность совета и уровня сложности.
        Отдаём: упражнения без coaching_tip.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            SpeechPracticeDTO(difficulty_label="Базовый")

    def test_lists_default_to_empty(self) -> None:
        """
        Тестируем: значения по умолчанию списков упражнений.
        Отдаём: набор только с обязательными полями.
        Ожидаем: слова, фразы и диалоги — пустые списки.
        """
        practice = SpeechPracticeDTO(coaching_tip="Говори медленно", difficulty_label="Базовый")

        assert practice.words == []
        assert practice.sentences == []
        assert practice.dialogues == []


class TestSpeechPracticePageDTO:
    """Группа тестов DTO страницы речевой практики."""

    def test_practice_is_optional(self) -> None:
        """
        Тестируем: необязательность сгенерированных упражнений.
        Отдаём: страницу до генерации.
        Ожидаем: practice и skill_summary равны None, списки пусты.
        """
        page = SpeechPracticePageDTO(title="Речь", subtitle="Подзаголовок", words_text="a, b")

        assert page.practice is None
        assert page.skill_summary is None
        assert page.suggested_words == []
        assert page.latest_topics == []
