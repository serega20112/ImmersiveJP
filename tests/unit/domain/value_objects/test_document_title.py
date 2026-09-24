"""Юнит-тесты value object DocumentTitle: нормализация и запрет пустых значений."""

import pytest

from src.domain.exceptions import InvalidDocumentTitleError
from src.domain.value_objects import DocumentTitle


class TestDocumentTitle:
    """Группа тестов заголовка пользовательского документа."""

    @pytest.mark.parametrize(
        "raw, expected",
        [("Конспект", "Конспект"), ("  title  ", "title")],
        ids=["plain", "trimmed"],
    )
    def test_accepts_and_normalizes(self, raw: str, expected: str) -> None:
        """
        Тестируем: создание заголовка документа.
        Отдаём: непустые строки с пробелами по краям.
        Ожидаем: значение сохранено с обрезкой пробелов.
        """
        assert DocumentTitle(raw).value == expected

    @pytest.mark.parametrize("invalid", ["", "   ", 42], ids=["empty", "whitespace", "not-str"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию заголовка документа.
        Отдаём: пустые строки и не-строку.
        Ожидаем: выброс InvalidDocumentTitleError.
        """
        with pytest.raises(InvalidDocumentTitleError):
            DocumentTitle(invalid)
