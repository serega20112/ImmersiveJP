"""Юнит-тесты value object TrackType: человекочитаемые подписи треков."""

import pytest

from src.domain.value_objects.track_type import TrackType


class TestTrackType:
    """Группа тестов типов учебных треков."""

    @pytest.mark.parametrize(
        "track, expected_title",
        [
            (TrackType.LANGUAGE, "Язык"),
            (TrackType.CULTURE, "Культура"),
            (TrackType.HISTORY, "История"),
        ],
        ids=["language", "culture", "history"],
    )
    def test_title_defined(self, track: TrackType, expected_title: str) -> None:
        """
        Тестируем: человекочитаемое название типа трека.
        Отдаём: каждый из трёх допустимых типов трека.
        Ожидаем: title совпадает с ожидаемым названием.
        """
        assert track.title == expected_title

    @pytest.mark.parametrize(
        "track",
        [TrackType.LANGUAGE, TrackType.CULTURE, TrackType.HISTORY],
        ids=["language", "culture", "history"],
    )
    def test_subtitle_defined(self, track: TrackType) -> None:
        """
        Тестируем: поясняющую подпись типа трека.
        Отдаём: каждый из трёх допустимых типов трека.
        Ожидаем: непустая subtitle для каждого варианта.
        """
        assert track.subtitle
