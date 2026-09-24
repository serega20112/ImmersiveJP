"""Разбор строк, которые генерирует нейросеть в карточках.

Пример употребления приходит из генерации одной строкой с разделителями, а
разбирается в двух местах: при показе карточки и при сборке заданий по
партии. Чтобы правила не разъезжались, разбор хранится здесь.
"""

from __future__ import annotations

_EXAMPLE_SEPARATOR = "|"
_EXAMPLE_FULL_PARTS = 3
_EXAMPLE_WITHOUT_ROMAJI = 2


def parse_example(example: str) -> dict[str, str | None]:
    """Разобрать строку примера употребления на части.

    Нейросеть возвращает пример строкой вида «японский|ромадзи|перевод».
    Допускаются сокращённые варианты: без ромадзи и вообще без разделения,
    а лишние части после третьей отбрасываются.

    Пропущенная часть возвращается как None, а не как пустая строка:
    отсутствие части и пустая часть значат разное для контракта DTO,
    который уходит в шаблон.

    Args:
        example: Исходная строка примера из карточки.

    Returns:
        Словарь с ключами japanese, romaji и translation.
    """
    parts = [part.strip() for part in example.split(_EXAMPLE_SEPARATOR)]
    if len(parts) >= _EXAMPLE_FULL_PARTS:
        return {"japanese": parts[0], "romaji": parts[1], "translation": parts[2]}
    if len(parts) == _EXAMPLE_WITHOUT_ROMAJI:
        return {"japanese": parts[0], "romaji": None, "translation": parts[1]}
    return {"japanese": example.strip(), "romaji": None, "translation": None}
