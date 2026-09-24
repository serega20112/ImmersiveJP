"""
Юнит-тесты мапперов application-слоя (use_cases/mappers).

Проверяются: конвертация агрегата User в UserViewDTO, карточки в
TrackCardDTO (включая очистку объяснения и парсинг примеров),
снимка прогресса и результата диагностики.
"""

from src.application.dto.learning import CardExampleDTO
from src.application.use_cases.mappers import (
    to_skill_assessment_dto,
    to_track_card_dto,
    to_track_progress_dto,
    to_user_view_dto,
)
from src.domain.entities.progress import TrackProgressSnapshot
from src.domain.value_objects import CardCount
from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.track_type import TrackType
from src.domain.value_objects.user import LanguageLevel
from tests.fixtures.factories.card_factory import CardFactory
from tests.fixtures.factories.user_factory import UserFactory


class TestToUserViewDTO:
    """Группа тестов маппинга агрегата пользователя."""

    def test_maps_all_fields(self, user_factory: UserFactory) -> None:
        """
        Тестируем: конвертацию агрегата User в UserViewDTO.
        Отдаём: пользователь с подтверждённым email и завершённым онбордингом.
        Ожидаем: DTO повторяет значения агрегата.
        """
        user = user_factory.build(user_id=5)
        user.is_email_verified = True

        dto = to_user_view_dto(user)

        assert dto.id == 5
        assert dto.email == "user@example.com"
        assert dto.display_name == "Сергей"
        assert dto.is_email_verified is True
        assert dto.onboarding_completed is False


class TestToTrackCardDTO:
    """Группа тестов маппинга учебной карточки."""

    def test_maps_fields_and_completion_flag(self) -> None:
        """
        Тестируем: конвертацию карточки в TrackCardDTO.
        Отдаём: карточка с id=2, примером "японский|ромадзи|перевод" и completed_ids={2}.
        Ожидаем: пример разобран на три поля, is_completed=True.
        """
        card = CardFactory(card_id=2, examples=["私は学生です|watashi wa gakusei desu|я студент"]).build()

        dto = to_track_card_dto(card, completed_ids={2})

        assert dto.id == 2
        assert dto.track == TrackType.LANGUAGE.value
        assert dto.is_completed is True
        assert dto.key_term_items
        example = dto.examples[0]
        assert isinstance(example, CardExampleDTO)
        assert example.japanese == "私は学生です"
        assert example.romaji == "watashi wa gakusei desu"
        assert example.translation == "я студент"

    def test_marks_card_incomplete_when_not_in_completed_ids(self) -> None:
        """
        Тестируем: карточку вне списка завершённых.
        Отдаём: карточка с id=3, completed_ids без 3.
        Ожидаем: is_completed=False.
        """
        card = CardFactory(card_id=3).build()

        dto = to_track_card_dto(card, completed_ids=set())

        assert dto.is_completed is False

    def test_example_without_translator_keeps_two_parts(self) -> None:
        """
        Тестируем: парсинг примера из двух частей.
        Отдаём: пример "японский|перевод".
        Ожидаем: DTO с пустым romaji и заполненным переводом.
        """
        card = CardFactory(card_id=1, examples=["こんにちは|здравствуйте"]).build()

        dto = to_track_card_dto(card, completed_ids=set())

        assert dto.examples[0].romaji is None
        assert dto.examples[0].translation == "здравствуйте"


class TestToTrackProgressDTO:
    """Группа тестов маппинга снимка прогресса."""

    def test_maps_progress_fields(self) -> None:
        """
        Тестируем: конвертацию снимка прогресса в DTO.
        Отдаём: снимок с половиной завершённых карточек.
        Ожидаем: track, счётчики и completion_rate переданы корректно.
        """
        snapshot = TrackProgressSnapshot(
            track=TrackType.LANGUAGE,
            completed_cards=CardCount(5),
            generated_cards=CardCount(10),
            current_batch=2,
            completed_batches=1,
            work_ready_batch=1,
        )

        dto = to_track_progress_dto(snapshot)

        assert dto.track == "language"
        assert dto.title == "Язык"
        assert dto.completed_cards == 5
        assert dto.generated_cards == 10
        assert dto.completion_rate == 50.0
        assert dto.work_ready_batch == 1


class TestToSkillAssessmentDTO:
    """Группа тестов маппинга результата диагностики."""

    def test_returns_none_for_none(self) -> None:
        """
        Тестируем: обработку отсутствующего результата диагностики.
        Отдаём: None вместо SkillAssessment.
        Ожидаем: None в ответе.
        """
        assert to_skill_assessment_dto(None) is None

    def test_maps_score_and_level(self) -> None:
        """
        Тестируем: конвертацию результата диагностики.
        Отдаём: оценка 40 с уровнем BASIC.
        Ожидаем: DTO с теми же значениями и человеческим названием уровня.
        """
        assessment = SkillAssessment(score=40, estimated_level=LanguageLevel.BASIC)

        dto = to_skill_assessment_dto(assessment)

        assert dto is not None
        assert dto.score == 40
        assert dto.estimated_level == "basic"
