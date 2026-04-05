from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    learning_goal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    interests_json: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


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
        ForeignKey("users.id", ondelete="CASCADE"), index=True
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


class CardCompletionModel(Base):
    __tablename__ = "card_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_card_completion_user_card"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
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


class LearningSessionModel(Base):
    __tablename__ = "learning_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "track", name="uq_learning_session_user_track"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    track: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    last_generated_batch: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
