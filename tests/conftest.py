"""Глобальные фикстуры pytest для всех уровней тестов.

Сюда попадает только тот "клей", который нужен тестам любого уровня:
корневой путь проекта и базовые фабрики. Специфичные моки интерфейсов
живут в conftest.py соответствующего уровня (unit/integration/e2e).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tests.fixtures.factories.card_factory import CardFactory
from tests.fixtures.factories.user_factory import UserFactory

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project_root() -> Path:
    """Корневая директория проекта (для путей к шаблонам и статике)."""
    return PROJECT_ROOT


@pytest.fixture
def user_factory() -> UserFactory:
    """Фабрика доменных пользователей с значениями по умолчанию."""
    return UserFactory()


@pytest.fixture
def card_factory() -> Callable[..., CardFactory]:
    """Фабрика учебных карточек; аргументы переопределяют значения полей."""

    def _factory(**overrides: object) -> CardFactory:
        return CardFactory(**overrides)

    return _factory
