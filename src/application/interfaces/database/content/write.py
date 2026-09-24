"""Порт записи репозитория учебных карточек."""

from __future__ import annotations

from abc import ABC

from src.application.interfaces.database.base.write import WriteRepositoryPort
from src.domain.entities import LearningCard


class LearningCardWriteRepositoryPort(WriteRepositoryPort[LearningCard, int], ABC):
    """Порт записи учебных карточек.

    Добавление и обновление одной карточки приходят из базового порта: партия
    дописывается по одной карточке, и отдельного пакетного метода не нужно.
    """
