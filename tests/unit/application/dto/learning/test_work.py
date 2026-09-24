"""
Юнит-тесты DTO работы по партии карточек.

Проверяются: значения по умолчанию заданий и результатов,
а также вложенность оценки прогресса и итогового результата.
"""

from src.application.dto.learning.work import (
    TrackWorkPageDTO,
    TrackWorkResultDTO,
    TrackWorkTaskDTO,
    TrackWorkTaskResultDTO,
    WorkHintDTO,
)


def _task(**overrides: object) -> TrackWorkTaskDTO:
    """Собрать минимальное корректное задание работы по партии."""
    payload = {
        "id": "t1",
        "kind": "translation",
        "title": "Перевод",
        "prompt": "Переведи",
        "expected_format": "текст",
        "source_topic": "Приветствие",
        "placeholder": "Ответ",
    }
    payload.update(overrides)
    return TrackWorkTaskDTO(**payload)


class TestWorkHintDTO:
    """Группа тестов DTO подсказки к заданию."""

    def test_keeps_title_and_content(self) -> None:
        """
        Тестируем: сохранение названия и текста подсказки.
        Отдаём: заполненную подсказку.
        Ожидаем: оба поля сохранены.
        """
        hint = WorkHintDTO(title="Подсказка", content="Помни про частицы")

        assert (hint.title, hint.content) == ("Подсказка", "Помни про частицы")


class TestTrackWorkTaskDTO:
    """Группа тестов DTO задания работы по партии."""

    def test_defaults_for_terms_hints_and_answer(self) -> None:
        """
        Тестируем: значения по умолчанию терминов, подсказок и ответа.
        Отдаём: задание без этих полей.
        Ожидаем: списки пусты, submitted_answer None.
        """
        task = _task()

        assert task.required_terms == []
        assert task.hints == []
        assert task.submitted_answer is None


class TestTrackWorkResultDTO:
    """Группа тестов DTO итогового результата работы."""

    def test_certificate_and_task_results_default(self) -> None:
        """
        Тестируем: значения по умолчанию сертификата и результатов заданий.
        Отдаём: результат без этих полей.
        Ожидаем: certificate_statement None, task_results пустой список.
        """
        result = TrackWorkResultDTO(
            score=8,
            pass_score=7,
            passed=True,
            summary="Резюме",
            verdict="Отлично",
        )

        assert result.certificate_statement is None
        assert result.task_results == []

    def test_task_result_optional_revealed_answer(self) -> None:
        """
        Тестируем: необязательность правильного ответа в результате задания.
        Отдаём: результат задания без revealed_answer.
        Ожидаем: поле равно None.
        """
        result = TrackWorkTaskResultDTO(task_id="t1", is_correct=False, feedback="Почти")

        assert result.revealed_answer is None


class TestTrackWorkPageDTO:
    """Группа тестов DTO страницы работы по партии."""

    def test_optional_trust_and_result(self) -> None:
        """
        Тестируем: необязательность оценки прогресса и результата.
        Отдаём: страницу до отправки ответов.
        Ожидаем: trust_score и result равны None, списки пусты.
        """
        page = TrackWorkPageDTO(
            track="jlpt",
            title="Работа",
            subtitle="Подзаголовок",
            batch_number=1,
            pass_score=7,
        )

        assert page.trust_score is None
        assert page.result is None
        assert page.source_topics == []
        assert page.tasks == []
