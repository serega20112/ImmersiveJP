"""
Юнит-тесты снимка прогресса TrackProgressSnapshot.

Проверяется вычисление процента завершения, переход к следующему батчу
и отметка батча как готового к проверке.
"""

import pytest

from src.domain.entities.progress import CARD_BATCH_SIZE, TrackProgressSnapshot
from src.domain.value_objects import CardCount
from src.domain.value_objects.track_type import TrackType


def _snapshot(completed: int, generated: int) -> TrackProgressSnapshot:
    """Собрать снимок прогресса с заданными счётчиками карточек.

    Args:
        completed: Количество завершённых карточек.
        generated: Количество сгенерированных карточек.

    Returns:
        Снимок прогресса по треку LANGUAGE.
    """
    return TrackProgressSnapshot(
        track=TrackType.LANGUAGE,
        completed_cards=CardCount(completed),
        generated_cards=CardCount(generated),
        current_batch=1,
    )


class TestTrackProgressSnapshot:
    """Группа тестов вычислений снимка прогресса."""

    def test_batch_size_constant_is_five(self) -> None:
        """
        Тестируем: константу размера батча.
        Отдаём: отсутствие входных данных.
        Ожидаем: CARD_BATCH_SIZE равен 5 и совпадает с BATCH_SIZE снимка.
        """
        assert CARD_BATCH_SIZE == 5
        assert TrackProgressSnapshot.BATCH_SIZE == CARD_BATCH_SIZE

    @pytest.mark.parametrize(
        "completed, generated, expected_rate",
        [
            (0, 0, 0.0),
            (0, 10, 0.0),
            (5, 10, 50.0),
            (10, 10, 100.0),
        ],
        ids=["empty", "nothing-completed", "half", "all"],
    )
    def test_completion_rate(
        self, completed: int, generated: int, expected_rate: float
    ) -> None:
        """
        Тестируем: вычисление процента завершения трека.
        Отдаём: пары счётчиков (завершено/сгенерировано) от пустого до полного.
        Ожидаем: CompletionRate соответствует доле завершённых карточек.
        """
        snapshot = _snapshot(completed, generated)

        assert snapshot.completion_rate.percentage == pytest.approx(expected_rate)

    def test_advance_batch_moves_to_next_batch(self) -> None:
        """
        Тестируем: переход к следующему батчу.
        Отдаём: снимок с current_batch=1 и completed_batches=0.
        Ожидаем: current_batch увеличен на 1, счётчик завершённых батчей вырос.
        """
        snapshot = _snapshot(5, 5)

        snapshot.advance_batch()

        assert snapshot.current_batch == 2
        assert snapshot.completed_batches == 1

    def test_mark_work_ready_records_current_batch(self) -> None:
        """
        Тестируем: отметку батча готовым к проверке.
        Отдаём: снимок с current_batch=2.
        Ожидаем: work_ready_batch равен 2.
        """
        snapshot = _snapshot(5, 5)
        snapshot.advance_batch()

        snapshot.mark_work_ready()

        assert snapshot.work_ready_batch == snapshot.current_batch == 2

