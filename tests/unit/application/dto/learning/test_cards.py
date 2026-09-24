"""
Юнит-тесты DTO учебных карточек.

Проверяются: значения по умолчанию примеров и терминов, обязательность
основных полей карточки и состав страниц трека и карточки.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.learning.cards import (
    CardCompletionResultDTO,
    CardExampleDTO,
    GeneratedCardDraftDTO,
    KeyTermDTO,
    TrackCardDTO,
    TrackCardPageDTO,
    TrackPageDTO,
)


def _card(**overrides: object) -> TrackCardDTO:
    """Собрать минимальную корректную учебную карточку."""
    payload = {
        "id": 1,
        "track": "jlpt",
        "topic": "Приветствие",
        "preview": "Превью",
        "explanation": "Объяснение",
        "examples": [],
        "key_terms": [],
        "batch_number": 1,
        "position": 1,
        "is_completed": False,
    }
    payload.update(overrides)
    return TrackCardDTO(**payload)


class TestCardExampleAndKeyTermDTO:
    """Группа тестов DTO примеров и ключевых терминов."""

    def test_example_optional_parts_default_to_none(self) -> None:
        """
        Тестируем: значения по умолчанию транслитерации и перевода примера.
        Отдаём: пример только с исходным и японским текстом.
        Ожидаем: romaji и translation равны None.
        """
        example = CardExampleDTO(raw_text="привет|こんにちは", japanese="こんにちは")

        assert example.romaji is None
        assert example.translation is None

    def test_key_term_optional_translation(self) -> None:
        """
        Тестируем: необязательность перевода термина.
        Отдаём: термин без перевода.
        Ожидаем: translation равно None.
        """
        assert KeyTermDTO(raw_text="こんにちは", label="привет").translation is None


class TestTrackCardDTO:
    """Группа тестов DTO учебной карточки."""

    def test_key_term_items_default_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию структурированных терминов.
        Отдаём: карточку без key_term_items.
        Ожидаем: поле — пустой список.
        """
        assert _card().key_term_items == []

    @pytest.mark.parametrize(
        "missing_field",
        ["id", "track", "topic", "preview", "explanation", "examples", "key_terms", "batch_number", "position", "is_completed"],
        ids=lambda name: name.replace("_", "-"),
    )
    def test_raises_when_required_field_missing(self, missing_field: str) -> None:
        """
        Тестируем: обязательность основных полей карточки.
        Отдаём: словарь полей без одного из обязательных ключей.
        Ожидаем: ValidationError.
        """
        payload = {
            "id": 1,
            "track": "jlpt",
            "topic": "t",
            "preview": "p",
            "explanation": "e",
            "examples": [],
            "key_terms": [],
            "batch_number": 1,
            "position": 1,
            "is_completed": False,
        }
        payload.pop(missing_field)

        with pytest.raises(ValidationError):
            TrackCardDTO(**payload)


class TestTrackPageDTO:
    """Группа тестов DTO страницы трека."""

    def test_optional_work_fields_default_to_none(self) -> None:
        """
        Тестируем: значения по умолчанию полей домашней работы.
        Отдаём: страницу трека без work_ready_batch и work_href.
        Ожидаем: оба поля равны None.
        """
        page = TrackPageDTO(
            track="jlpt",
            title="JLPT",
            subtitle="Подзаголовок",
            cards=[],
            current_batch=1,
            completed_total=0,
            generated_total=5,
            all_current_batch_completed=False,
            can_generate_next=False,
            generate_action_label="Сгенерировать",
            completed_batches=0,
        )

        assert page.work_ready_batch is None
        assert page.work_href is None


class TestTrackCardPageDTO:
    """Группа тестов DTO страницы отдельной карточки."""

    def test_nests_card_and_batch_cards(self) -> None:
        """
        Тестируем: вложенность текущей карточки и списка карточек партии.
        Отдаём: карточку и партию из двух карточек.
        Ожидаем: обе части доступны через поля страницы.
        """
        card = _card(id=2, position=2)

        page = TrackCardPageDTO(
            track="jlpt",
            title="JLPT",
            subtitle="Подзаголовок",
            card=card,
            batch_cards=[_card(id=1), card],
            current_batch=1,
            completed_total=1,
            generated_total=2,
            all_current_batch_completed=False,
            can_generate_next=False,
            completed_batches=0,
        )

        assert page.card.id == 2
        assert len(page.batch_cards) == 2


class TestCardCompletionAndDraftDTO:
    """Группа тестов DTO завершения карточки и черновика генерации."""

    def test_completion_result_keeps_flag(self) -> None:
        """
        Тестируем: DTO результата завершения карточки.
        Отдаём: идентификаторы и флаг завершения партии.
        Ожидаем: флаг сохранён.
        """
        result = CardCompletionResultDTO(card_id=1, track="jlpt", batch_completed=True)

        assert result.batch_completed is True

    def test_draft_keeps_examples_and_terms(self) -> None:
        """
        Тестируем: DTO черновика карточки от нейросети.
        Отдаём: тему, объяснение, примеры и термины.
        Ожидаем: списки сохранены без изменений.
        """
        draft = GeneratedCardDraftDTO(
            topic="Тема",
            explanation="Объяснение",
            examples=["a", "b"],
            key_terms=["term"],
        )

        assert draft.examples == ["a", "b"]
        assert draft.key_terms == ["term"]
