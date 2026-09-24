from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructures.database.database import Base


class CourseTopicModel(Base):
    """Тема учебной программы — минимальная единица изучения.

    Именно к теме в дальнейшем привязывается усвоение: модуль и этап слишком
    крупны, чтобы честно сказать «вот это уже можно пропустить».

    Поля:
        id: Первичный ключ.
        module_id: Принадлежность к модулю (course_modules.id, каскадное удаление).
        title: Название темы.
        position: Порядок темы внутри модуля.
    """

    __tablename__ = "course_topics"
    __table_args__ = (
        UniqueConstraint("module_id", "position", name="uq_course_topics_module_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("course_modules.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    module = relationship("CourseModuleModel", back_populates="topics")
