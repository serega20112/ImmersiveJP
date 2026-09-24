from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructures.database.database import Base
from src.infrastructures.database.models.course_topic_model import CourseTopicModel


class CourseModuleModel(Base):
    """Модуль учебной программы внутри этапа.

    Модуль группирует темы одной грани этапа: чтение, частицы, глаголы.
    code строится с префиксом этапа, поэтому повторяющиеся названия
    («Словарь», «Кандзи») на разных этапах остаются разными идентификаторами.

    Поля:
        id: Первичный ключ.
        stage_id: Принадлежность к этапу (course_stages.id, каскадное удаление).
        code: Устойчивый программный идентификатор модуля.
        title: Название модуля.
        position: Порядок модуля внутри этапа.
    """

    __tablename__ = "course_modules"
    __table_args__ = (
        UniqueConstraint("code", name="uq_course_modules_code"),
        UniqueConstraint("stage_id", "position", name="uq_course_modules_stage_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("course_stages.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(96), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    stage = relationship("CourseStageModel", back_populates="modules")
    topics: Mapped[list[CourseTopicModel]] = relationship(
        CourseTopicModel,
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="CourseTopicModel.position",
    )
