"""
Юнит-тесты парсера ключевых терминов (use_cases/key_terms).

Проверяются: разбор форматов "термин (перевод)", разделителей,
словаря переводов, дедупликация и значения для промптов/инпутов.
"""

from __future__ import annotations

import pytest

from src.application.dto.learning import KeyTermDTO
from src.application.use_cases.key_terms import (
    build_key_term_dtos,
    key_term_input_value,
    key_term_prompt_value,
    parse_key_term,
)


class TestParseKeyTerm:
    """Группа тестов разбора строки термина."""

    def test_parses_bracket_format(self) -> None:
        """
        Тестируем: формат "термин (перевод)".
        Отдаём: строку "挨拶 (приветствие)".
        Ожидаем: кортеж ("挨拶", "приветствие").
        """
        assert parse_key_term("挨拶 (приветствие)") == ("挨拶", "приветствие")

    @pytest.mark.parametrize(
        "raw",
        ["挨拶 - приветствие", "挨拶 — приветствие", "挨拶: приветствие", "挨拶 | приветствие"],
        ids=["dash", "emdash", "colon", "pipe"],
    )
    def test_parses_separator_formats(self, raw: str) -> None:
        """
        Тестируем: форматы с разделителями.
        Отдаём: строки с разными разделителями между термином и переводом.
        Ожидаем: одинаковый кортеж ("挨拶", "приветствие").
        """
        assert parse_key_term(raw) == ("挨拶", "приветствие")

    def test_known_term_translated_without_annotation(self) -> None:
        """
        Тестируем: термин из встроенного словаря без перевода.
        Отдаём: строку "駅".
        Ожидаем: перевод "станция" из словаря.
        """
        assert parse_key_term("駅") == ("駅", "станция")

    def test_empty_term_returns_empty_label(self) -> None:
        """
        Тестируем: обработку пустой строки.
        Отдаём: пустую строку.
        Ожидаем: кортеж ("", None).
        """
        assert parse_key_term("   ") == ("", None)


class TestBuildKeyTermDTOs:
    """Группа тестов сборки DTO терминов."""

    def test_deduplicates_and_skips_empty(self) -> None:
        """
        Тестируем: дедупликацию и пропуск пустых терминов.
        Отдаём: список с дублем и пустыми элементами.
        Ожидаем: два уникальных KeyTermDTO в порядке следования.
        """
        dtos = build_key_term_dtos(["挨拶 (приветствие)", "", "挨拶 (приветствие)", "駅 (станция)"])

        assert all(isinstance(dto, KeyTermDTO) for dto in dtos)
        assert [dto.label for dto in dtos] == ["挨拶", "駅"]

    def test_keeps_raw_text(self) -> None:
        """
        Тестируем: сохранение исходной строки термина.
        Отдаём: термин с аннотацией.
        Ожидаем: raw_text равен исходной строке.
        """
        dto = build_key_term_dtos(["挨拶 (приветствие)"])[0]

        assert dto.raw_text == "挨拶 (приветствие)"


class TestPromptAndInputValues:
    """Группа тестов значений для промптов и полей ввода."""

    def test_prompt_value_prefers_translation(self) -> None:
        """
        Тестируем: значение для промпта.
        Отдаём: термин с переводом.
        Ожидаем: перевод вместо исходного термина.
        """
        assert key_term_prompt_value("挨拶 (приветствие)") == "приветствие"

    def test_input_value_joins_label_and_translation(self) -> None:
        """
        Тестируем: отображаемое значение для поля ввода.
        Отдаём: термин с переводом.
        Ожидаем: строку "термин - перевод".
        """
        assert key_term_input_value("挨拶 (приветствие)") == "挨拶 - приветствие"

    def test_input_value_label_only_without_translation(self) -> None:
        """
        Тестируем: отображаемое значение без перевода.
        Отдаём: неизвестный термин без аннотации.
        Ожидаем: только сам термин.
        """
        assert key_term_input_value("未知の語") == "未知の語"
