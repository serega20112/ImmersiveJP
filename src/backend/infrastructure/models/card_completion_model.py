from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.infrastructure.files.database import Base


class CardCompletionModel(Base):
    __tablename__ = "card_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_card_completion_user_card"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("learning_cards.id", ondelete="CASCADE"),
        index=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
