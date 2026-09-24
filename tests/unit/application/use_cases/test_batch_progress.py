"""Юнит-тесты сводки завершённых батчей (use_cases/batch_progress)."""

from src.application.use_cases.batch_progress import summarize_completed_batches
from src.domain.value_objects.track_type import TrackType


class _FakeProgressRepository:
    """Заглушка ProgressRepositoryPort с заданным множеством завершённых батчей."""

    def __init__(self, completed: set[int]) -> None:
        """Инициализировать заглушку множеством завершённых батчей.

        Args:
            completed: Номера батчей, считающихся завершёнными.
        """
        self._completed = completed

    async def is_batch_completed(self, user_id: int, track: TrackType, batch_number: int) -> bool:  # noqa: ARG002
        """Сообщить, завершён ли батч.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            batch_number: Номер батча.

        Returns:
            True для батчей из списка завершённых.
        """
        return batch_number in self._completed


class TestSummarizeCompletedBatches:
    """Группа тестов сводки по завершённым батчам."""

    async def test_returns_zero_for_first_batch(self) -> None:
        """
        Тестируем: обработку первого (ещё не завершённого) батча.
        Отдаём: current_batch=0.
        Ожидаем: (0, None) без обращения к репозиторию.
        """
        repository = _FakeProgressRepository(completed=set())

        result = await summarize_completed_batches(repository, user_id=1, track=TrackType.LANGUAGE, current_batch=0)

        assert result == (0, None)

    async def test_counts_completed_and_reports_work_ready(self) -> None:
        """
        Тестируем: подсчёт завершённых батчей и последнего готового к проверке.
        Отдаём: завершены батчи 1 и 3 из четырёх.
        Ожидаем: count=2, work_ready=3 (последний завершённый).
        """
        repository = _FakeProgressRepository(completed={1, 3})

        result = await summarize_completed_batches(repository, user_id=1, track=TrackType.LANGUAGE, current_batch=4)

        assert result == (2, 3)

    async def test_counts_nothing_when_no_batch_completed(self) -> None:
        """
        Тестируем: ситуацию без завершённых батчей.
        Отдаём: current_batch=3, завершённых нет.
        Ожидаем: (0, None).
        """
        repository = _FakeProgressRepository(completed=set())

        result = await summarize_completed_batches(repository, user_id=1, track=TrackType.LANGUAGE, current_batch=3)

        assert result == (0, None)
