"""
Юнит-тесты сущности LearningCard.

Проверяются фабрика create (приведение типов value objects) и метод
preview (нормализация пробелов, обрезка и завершение многоточием).
"""

from src.domain.entities.content import LearningCard
from src.domain.value_objects import BatchNumber, CardPosition, LearningCardID
from src.domain.value_objects.track_type import TrackType


class TestLearningCard:
    """Группа тестов сущности учебной карточки."""

    def test_create_coerces_scalar_fields(self) -> None:
        """
        Тестируем: фабричный метод create со скалярными аргументами.
        Отдаём: числовые user_id/batch/position и card_id без value objects.
        Ожидаем: все поля приведены к доменным value objects.
        """
        card = LearningCard.create(
            user_id=1,
            track=TrackType.LANGUAGE,
            topic="私",
            explanation="Местоимение",
            examples=["私は学生です"],
            key_terms=["私"],
            batch_number=2,
            position=3,
            card_id=10,
        )

        assert card.user_id.value == 1
        assert card.id == LearningCardID(10)
        assert card.batch_number == BatchNumber(2)
        assert card.position == CardPosition(3)

    def test_create_generates_timestamp(self) -> None:
        """
        Тестируем: автогенерацию времени создания.
        Отдаём: create без created_at.
        Ожидаем: created_at заполнен текущим моментом (value object Timestamp).
        """
        card = LearningCard.create(
            user_id=1,
            track=TrackType.LANGUAGE,
            topic="私",
            explanation="Местоимение",
            examples=[],
            key_terms=[],
            batch_number=1,
            position=1,
        )

        assert card.created_at is not None

    def test_preview_compacts_whitespace(self) -> None:
        """
        Тестируем: превью с нормализацией пробелов.
        Отдаём: объяснение с лишними переносами и пробелами.
        Ожидаем: строка без повторных пробелов, короче лимита.
        """
        card = LearningCard.create(
            user_id=1,
            track=TrackType.LANGUAGE,
            topic="私",
            explanation="Строка  с   несколькими\n\nпробелами и переносами",
            examples=[],
            key_terms=[],
            batch_number=1,
            position=1,
        )

        preview = card.preview()

        assert "  " not in preview
        assert "\n" not in preview

    def test_preview_truncates_long_text(self) -> None:
        """
        Тестируем: обрезку длинного объяснения.
        Отдаём: текст длиннее 170 символов.
        Ожидаем: превью не длиннее лимита и завершается многоточием.
        """
        card = LearningCard.create(
            user_id=1,
            track=TrackType.LANGUAGE,
            topic="私",
            explanation="слово " * 60,
            examples=[],
            key_terms=[],
            batch_number=1,
            position=1,
        )

        preview = card.preview(max_length=170)

        assert len(preview) <= 170
        assert preview.endswith("...")
