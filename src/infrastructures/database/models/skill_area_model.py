from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructures.database.database import Base


class SkillAreaModel(Base):
    """Справочник областей навыков диагностики.

    Таблица связывает две системы координат: что замеряет диагностика и какой
    этап программы за это отвечает. Ссылка на этап идёт по position, а не по
    id, потому что position используется в расчётах темпа и горизонта.

    Поля:
        id: Первичный ключ.
        code: Устойчивый программный идентификатор области.
        title: Название области для человека и промптов.
        stage_position: Позиция этапа программы (course_stages.position).
        coaching_tip: Подсказка для речевой практики.
    """

    __tablename__ = "skill_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    stage_position: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "course_stages.position",
            name="fk_skill_areas_stage_position",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    coaching_tip: Mapped[str | None] = mapped_column(String(400), nullable=True)
