from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.infrastructure.files.database import Base


class LearningCardModel(Base):
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
    key_terms_json: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
