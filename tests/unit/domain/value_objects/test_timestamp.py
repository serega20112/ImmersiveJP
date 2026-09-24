"""Юнит-тесты value object Timestamp: UTC-нормализация и монотонность refresh."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.domain.exceptions import InvalidTimestampValueError
from src.domain.value_objects import Timestamp


class TestTimestamp:
    """Группа тестов момента времени с часовым поясом."""

    def test_now_fixes_utc_moment(self) -> None:
        """
        Тестируем: фабричный метод now.
        Отдаём: отсутствие входных данных.
        Ожидаем: значение в UTC и близко к текущему моменту.
        """
        before = datetime.now(UTC) - timedelta(seconds=5)
        timestamp = Timestamp.now()
        after = datetime.now(UTC) + timedelta(seconds=5)

        assert timestamp.value.tzinfo is UTC
        assert before <= timestamp.value <= after

    def test_normalizes_timezone_to_utc(self) -> None:
        """
        Тестируем: приведение произвольного часового пояса к UTC.
        Отдаём: datetime со смещением +05:00.
        Ожидаем: значение приведено к UTC с сохранением момента.
        """
        local_value = datetime(2026, 1, 1, 10, 0, tzinfo=timezone(timedelta(hours=5)))

        timestamp = Timestamp(local_value)

        assert timestamp.value.tzinfo is UTC
        assert timestamp.value == datetime(2026, 1, 1, 5, 0, tzinfo=UTC)

    def test_raises_on_naive_datetime(self) -> None:
        """
        Тестируем: запрет datetime без часового пояса.
        Отдаём: naive datetime.
        Ожидаем: выброс InvalidTimestampValueError.
        """
        with pytest.raises(InvalidTimestampValueError):
            Timestamp(datetime(2026, 1, 1))

    def test_refresh_moves_forward(self) -> None:
        """
        Тестируем: refresh возвращает новый момент, не раньше предыдущего.
        Отдаём: timestamp, зафиксированный ранее.
        Ожидаем: новое значение >= прежнего.
        """
        timestamp = Timestamp.now()

        refreshed = timestamp.refresh()

        assert refreshed.value >= timestamp.value
