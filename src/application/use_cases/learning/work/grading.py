"""Детерминированная оценка работы по партии карточек."""

from __future__ import annotations

from src.application.dto.learning import (
    PreparedWorkTaskDTO,
    TrackWorkResultDTO,
    TrackWorkTaskResultDTO,
)
from src.application.use_cases.learning.work.answer_check import answer_matches
from src.domain.value_objects.track_type import TrackType

WORK_PASS_SCORE = 80
WORK_CERTIFICATE_SCORE = 100
_FREE_FORM_KINDS = frozenset({"production", "immersion"})
_PERCENT = 100
_PASS_SUMMARY = "Материал по этой партии держится уверенно."
_MISS_SUMMARY = "По партии еще есть пробелы. Лучше еще раз пройти карточки и повторить работу."
_PASS_VERDICT = "Система видит, что этот набор уже можно использовать в коротких ответах и сценах."
_MISS_VERDICT = "Система пока не уверена, что этот набор закрепился в практике."
_CERTIFICATE_STATEMENT = (
    "По этой партии система считает, что бытовые конструкции используются "
    "без заметной опоры на подсказки."
)
_FREE_FORM_PASS_FEEDBACK = "Задание закрыто: нужный материал использован в ответе."
_FREE_FORM_MISS_FEEDBACK = "В ответе не хватает нужных элементов из пройденного материала."
_RECALL_PASS_FEEDBACK = "Ответ совпадает с материалом партии."
_RECALL_MISS_FEEDBACK = "Ответ не совпал с тем, что было в карточках этой партии."


def evaluate_work_submission(
    tasks: list[PreparedWorkTaskDTO],
    answers: dict[str, str],
    *,
    track: TrackType,
) -> TrackWorkResultDTO:
    """Проверить ответы и собрать результат по работе целиком.

    Оценка не зависит от нейросети: она служит запасным вариантом, когда
    модель проверки недоступна, и опорой для формулировки вердикта. Правила
    засчёта конкретного ответа живут в answer_check, здесь остаются подсчёт
    баллов и выбор формулировок для пользователя.

    Args:
        tasks: Задания, собранные по партии.
        answers: Ответы пользователя, где ключ — идентификатор задания.
        track: Тип трека обучения.

    Returns:
        Результат работы с баллами, вердиктом и обратной связью по заданиям.
    """
    task_results: list[TrackWorkTaskResultDTO] = []
    correct = 0

    for task in tasks:
        answer = str(answers.get(task.id) or "").strip()
        is_correct = answer_matches(task, answer)
        if is_correct:
            correct += 1
        task_results.append(
            TrackWorkTaskResultDTO(
                task_id=task.id,
                is_correct=is_correct,
                feedback=_feedback(task, is_correct),
                revealed_answer=None if is_correct else task.revealed_answer,
            )
        )

    score = round((correct / len(tasks)) * _PERCENT) if tasks else 0
    passed = score >= WORK_PASS_SCORE

    return TrackWorkResultDTO(
        score=score,
        pass_score=WORK_PASS_SCORE,
        passed=passed,
        summary=_PASS_SUMMARY if passed else _MISS_SUMMARY,
        verdict=_PASS_VERDICT if passed else _MISS_VERDICT,
        certificate_statement=_certificate(track, score, passed),
        task_results=task_results,
    )


def _feedback(task: PreparedWorkTaskDTO, is_correct: bool) -> str:
    """Подобрать формулировку обратной связи по заданию.

    Args:
        task: Проверенное задание.
        is_correct: Засчитан ли ответ.

    Returns:
        Текст для показа пользователю.
    """
    if task.kind in _FREE_FORM_KINDS:
        return _FREE_FORM_PASS_FEEDBACK if is_correct else _FREE_FORM_MISS_FEEDBACK
    return _RECALL_PASS_FEEDBACK if is_correct else _RECALL_MISS_FEEDBACK


def _certificate(track: TrackType, score: int, passed: bool) -> str | None:
    """Решить, выдавать ли отметку о полном закрытии партии.

    Отметка положена только языковому треку: именно в нём ответ без подсказок
    означает, что конструкция реально держится в речи.

    Args:
        track: Тип трека обучения.
        score: Набранные баллы.
        passed: Зачтена ли работа.

    Returns:
        Текст отметки либо None, если условий для неё нет.
    """
    if passed and track == TrackType.LANGUAGE and score >= WORK_CERTIFICATE_SCORE:
        return _CERTIFICATE_STATEMENT
    return None
