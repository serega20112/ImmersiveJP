"""Юнит-тесты сущности LearningSession: фабрика create и продвижение батча."""

from src.domain.entities.session import LearningSession
from src.domain.value_objects import UserID
from src.domain.value_objects.track_type import TrackType


class TestLearningSession:
    """Группа тестов учебной сессии."""

    def test_create_starts_from_zero_batch(self) -> None:
        """
        Тестируем: фабричный метод create учебной сессии.
        Отдаём: идентификатор пользователя и тип трека.
        Ожидаем: сессия с last_generated_batch=0 и заполненным updated_at.
        """
        session = LearningSession.create(UserID(1), TrackType.LANGUAGE)

        assert session.last_generated_batch == 0
        assert session.updated_at is not None

    def test_advance_batch_increments_and_touches_timestamp(self) -> None:
        """
        Тестируем: продвижение счётчика сгенерированных батчей.
        Отдаём: сессия с батчем 0.
        Ожидаем: last_generated_batch увеличен, updated_at обновлён.
        """
        session = LearningSession.create(UserID(1), TrackType.LANGUAGE)
        previous = session.updated_at

        session.advance_batch()

        assert session.last_generated_batch == 1
        assert session.updated_at.value >= previous.value
