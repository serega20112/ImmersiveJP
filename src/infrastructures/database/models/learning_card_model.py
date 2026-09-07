from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructures.database.database import Base


class LearningCardModel(Base):
    """Учебная карточка пользователя.

    Поля:
        id: Первичный ключ.
        user_id: Владелец карточки (users.id, каскадное удаление).
        track: Ключ трека обучения (language, culture, history).
        topic: Тема карточки.
        explanation: Основное объяснение темы.
        examples_json: Список примеров употребления.
        key_terms_json: Список ключевых терминов.
        batch_number: Номер батча, к которому относится карточка.
        position: Позиция карточки внутри батча.
        created_at: Момент создания записи (UTC).
    """

    __tablename__ = "learning_cards"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "track",
            "batch_number",
            "position",
            name="uq_learning_cards_position",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    track: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    examples_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    key_terms_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
