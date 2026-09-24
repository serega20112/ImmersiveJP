from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructures.database.database import Base


class LearningSessionModel(Base):
    """Учебная сессия пользователя по треку.

    Состояние генерации партии хранится здесь же, а не в памяти процесса:
    фоновая задача должна переживать перезапуск сервиса, а страница —
    перезагрузку, иначе пользователь навсегда остаётся с «готовим партию».

    Поля:
        id: Первичный ключ.
        user_id: Владелец сессии (users.id, каскадное удаление).
        track: Ключ трека обучения (language, culture, history).
        last_generated_batch: Номер последнего сгенерированного батча.
        updated_at: Момент последнего обновления записи (UTC).
        generation_state: Состояние генерации партии (ready, generating, failed).
        generation_started_at: Момент брони партии либо None для готовых партий.
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
    generation_state: Mapped[str] = mapped_column(
        String(16),
        server_default=text("'ready'"),
        nullable=False,
    )
    generation_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
