"""Порт чтения справочника областей навыков."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.skill_area import SkillArea


class SkillAreaReadRepositoryPort(ABC):
    """Порт доступа к областям навыков диагностики."""

    @abstractmethod
    async def list_areas(self) -> list[SkillArea]:
        """Получить все области навыков."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_code(self, code: str) -> SkillArea | None:
        """Получить область навыков по её программному идентификатору."""
        raise NotImplementedError
