"""SQLAlchemy-реализация репозитория учебной программы."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.application.interfaces.database import CourseRepositoryPort
from src.domain.entities.course import CourseModule, CourseStage, CourseTopic
from src.infrastructures.database.models import CourseModuleModel, CourseStageModel


class CourseRepository(CourseRepositoryPort):
    """Репозиторий учебной программы поверх PostgreSQL/SQLAlchemy.

    Читает справочные таблицы, заполняемые миграцией. Модули и темы
    подгружаются сразу, чтобы сборка страницы плана не зависела от ленивой
    загрузки и не делала по запросу на каждый этап.
    """

    def __init__(self, session) -> None:
        """Инициализировать репозиторий.

        Args:
            session: Сессия SQLAlchemy, предоставляемая Unit of Work.
        """
        self._session = session

    async def list_stages(self) -> list[CourseStage]:
        """Получить все этапы программы, упорядоченные по позиции.

        Returns:
            Список этапов с модулями и темами; пустой, если программа не
            заполнена.
        """
        statement = (
            select(CourseStageModel)
            .options(selectinload(CourseStageModel.modules).selectinload(CourseModuleModel.topics))
            .order_by(CourseStageModel.position)
        )
        result = await self._session.execute(statement)
        return [self.to_entity(model) for model in result.scalars().unique().all()]

    async def get_stage(self, code: str) -> CourseStage | None:
        """Получить этап по программному идентификатору.

        Args:
            code: Устойчивый идентификатор этапа.

        Returns:
            Этап либо None, если такого идентификатора нет.
        """
        statement = (
            select(CourseStageModel)
            .where(CourseStageModel.code == code)
            .options(selectinload(CourseStageModel.modules).selectinload(CourseModuleModel.topics))
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model is not None else None

    def to_entity(self, model: CourseStageModel) -> CourseStage:
        """Преобразовать ORM-модель этапа в доменную сущность.

        Args:
            model: ORM-модель этапа со связанными модулями.

        Returns:
            Доменный этап программы.
        """
        return CourseStage(
            id=model.id,
            code=model.code,
            title=model.title,
            timeframe=model.timeframe,
            summary=model.summary,
            position=model.position,
            modules=[self._to_module(module) for module in model.modules],
        )

    @staticmethod
    def _to_module(model: CourseModuleModel) -> CourseModule:
        """Преобразовать ORM-модель модуля в доменную сущность.

        Args:
            model: ORM-модель модуля со связанными темами.

        Returns:
            Доменный модуль программы.
        """
        return CourseModule(
            id=model.id,
            code=model.code,
            title=model.title,
            position=model.position,
            topics=[
                CourseTopic(id=topic.id, title=topic.title, position=topic.position)
                for topic in model.topics
            ],
        )
