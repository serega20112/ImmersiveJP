"""
Утилиты для работы с optional-значениями и value objects.

Содержит универсальные функции для преобразования между примитивными типами
и value objects, а также их nullable-версиями.
"""

from collections.abc import Callable
from typing import TypeVar

V = TypeVar("V")
VO = TypeVar("VO", covariant=True)


def to_optional(value: V | None, constructor: Callable[[V], VO]) -> VO | None:
    """
    Применить конструктор к значению, если оно не None.

    Args:
        value: исходное значение (может быть None);
        constructor: Callable, принимающий значение и возвращающий value object.

    Returns:
        Value object или None.
    """
    return constructor(value) if value is not None else None


def value_or_none(vo: VO | None) -> V | None:
    """
    Извлечь внутреннее значение из value-объекта, если он не None.

    Args:
        vo: Экземпляр value-объекта или None.

    Returns:
        None или "простой" тип данных - int, str, uuid, bool...
    """
    return getattr(vo, "value", vo)
