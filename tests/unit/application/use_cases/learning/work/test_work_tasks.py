"""
Юнит-тесты конструктора учебных заданий (learning/work/work_tasks).

Проверяются: пустой набор карточек, состав заданий языкового трека,
задания контекстных треков и маппинг подготовленного задания в DTO.
"""

from src.application.dto.learning import TrackWorkTaskDTO
from src.application.use_cases.learning.work.task_builder import build_prepared_work_tasks
from src.application.use_cases.mappers import to_track_work_task_dto
from src.domain.value_objects.track_type import TrackType

LANGUAGE_TASK_IDS = {"reading", "meaning", "recall", "scene", "confidence"}


class TestBuildPreparedWorkTasks:
    """Группа тестов сборки заданий по треку."""

    def test_returns_empty_list_without_cards(self) -> None:
        """
        Тестируем: обработку пустого батча карточек.
        Отдаём: пустой список карточек.
        Ожидаем: пустой список заданий.
        """
        assert build_prepared_work_tasks(TrackType.LANGUAGE, []) == []

    def test_language_track_builds_five_tasks(self, card_factory) -> None:
        """
        Тестируем: сборку заданий языкового трека.
        Отдаём: одна карточка LANGUAGE с ключевыми терминами.
        Ожидаем: пять заданий с известными id, у каждого заполнены заголовок и промпт.
        """
        card = card_factory().build()

        tasks = build_prepared_work_tasks(TrackType.LANGUAGE, [card])

        assert {task.id for task in tasks} == LANGUAGE_TASK_IDS
        assert all(task.title and task.prompt for task in tasks)

    def test_context_track_builds_tasks_with_fields(self, card_factory) -> None:
        """
        Тестируем: сборку заданий контекстного трека (CULTURE).
        Отдаём: одна карточка CULTURE с ключевыми терминами.
        Ожидаем: непустой список заданий; id уникальны; у каждого заполнены
                 промпт и формат ответа.
        """
        card = card_factory(track=TrackType.CULTURE).build()

        tasks = build_prepared_work_tasks(TrackType.CULTURE, [card])

        assert len(tasks) >= 1
        assert len({task.id for task in tasks}) == len(tasks)
        assert all(task.prompt and task.expected_format for task in tasks)


class TestToTrackWorkTaskDTO:
    """Группа тестов маппинга PreparedWorkTask в DTO."""

    def test_maps_fields_and_submitted_answer(self, card_factory) -> None:
        """
        Тестируем: преобразование подготовленного задания в TrackWorkTaskDTO.
        Отдаём: задание языкового трека и ответ пользователя.
        Ожидаем: DTO содержит id/kind/prompt задания и переданный ответ.
        """
        card = card_factory().build()
        task = build_prepared_work_tasks(TrackType.LANGUAGE, [card])[0]

        dto = to_track_work_task_dto(task, submitted_answer="мой ответ")

        assert isinstance(dto, TrackWorkTaskDTO)
        assert dto.id == task.id
        assert dto.kind == task.kind
        assert dto.prompt == task.prompt
        assert dto.submitted_answer == "мой ответ"
