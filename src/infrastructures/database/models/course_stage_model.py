from __future__ import annotations

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructures.database.database import Base
from src.infrastructures.database.models.course_module_model import CourseModuleModel


class CourseStageModel(Base):
    """Этап учебной программы.

    Справочная таблица: заполняется миграцией и не меняется из приложения.
    code служит устойчивым идентификатором для кода и внешних ссылок, а title
    и summary — только для показа человеку.

    Поля:
        id: Первичный ключ.
        code: Устойчивый программный идентификатор этапа.
        title: Название этапа.
        timeframe: Ориентир по срокам.
        summary: Описание этапа.
        position: Порядок этапа в программе.
    """

    __tablename__ = "course_stages"
    __table_args__ = (
        UniqueConstraint("code", name="uq_course_stages_code"),
        UniqueConstraint("position", name="uq_course_stages_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    modules: Mapped[list[CourseModuleModel]] = relationship(
        CourseModuleModel,
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="CourseModuleModel.position",
    )
