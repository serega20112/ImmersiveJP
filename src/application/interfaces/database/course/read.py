"""Порт чтения учебной программы."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.course import CourseStage


class CourseReadRepositoryPort(ABC):
    """Порт доступа к справочной учебной программе."""

    @abstractmethod
    async def list_stages(self) -> list[CourseStage]:
        """Получить все этапы программы вместе с модулями и темами."""
        raise NotImplementedError

    @abstractmethod
    async def get_stage(self, code: str) -> CourseStage | None:
        """Получить этап по его программному идентификатору."""
        raise NotImplementedError
