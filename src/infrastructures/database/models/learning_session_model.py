from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructures.database.database import Base


class LearningSessionModel(Base):
    """Учебная сессия пользователя по треку.

    Поля:
        id: Первичный ключ.
        user_id: Владелец сессии (users.id, каскадное удаление).
        track: Ключ трека обучения (language, culture, history).
        last_generated_batch: Номер последнего сгенерированного батча.
        updated_at: Момент последнего обновления записи (UTC).
    """

    __tablename__ = "learning_sessions"
    __table_args__ = (UniqueConstraint("user_id", "track", name="uq_learning_session_user_track"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    track: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    last_generated_batch: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
