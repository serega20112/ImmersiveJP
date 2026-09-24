"""SQLAlchemy-реализация репозитория областей навыков."""

from __future__ import annotations

from sqlalchemy import select

from src.application.interfaces.database import SkillAreaRepositoryPort
from src.domain.entities.skill_area import SkillArea
from src.infrastructures.database.models import SkillAreaModel


class SkillAreaRepository(SkillAreaRepositoryPort):
    """Репозиторий областей навыков поверх PostgreSQL/SQLAlchemy."""

    def __init__(self, session) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Сессия SQLAlchemy, предоставляемая Unit of Work.
        """
        self._session = session

    async def list_areas(self) -> list[SkillArea]:
        """Получить все области навыков в стабильном порядке.

        Returns:
            Список областей, упорядоченных по коду; пустой, если справочник
            не заполнен.
        """
        statement = select(SkillAreaModel).order_by(SkillAreaModel.code)
        result = await self._session.execute(statement)
        return [self.to_entity(model) for model in result.scalars().all()]

    async def get_by_code(self, code: str) -> SkillArea | None:
        """Получить область навыков по программному идентификатору.

        Args:
            code: Идентификатор области.

        Returns:
            Область либо None, если такого идентификатора нет.
        """
        statement = select(SkillAreaModel).where(SkillAreaModel.code == code)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model is not None else None

    @staticmethod
    def to_entity(model: SkillAreaModel) -> SkillArea:
        """Преобразовать ORM-модель в доменную сущность.

        Args:
            model: ORM-модель области навыков.

        Returns:
            Доменная область навыков.
        """
        return SkillArea(
            code=model.code,
            title=model.title,
            stage_position=model.stage_position,
            coaching_tip=model.coaching_tip,
        )
