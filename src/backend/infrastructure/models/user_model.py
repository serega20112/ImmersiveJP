from __future__ import annotations

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.infrastructure.files.database import Base
from src.backend.infrastructure.models.timestamp import TimestampMixin


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    learning_goal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    study_timeline: Mapped[str | None] = mapped_column(String(32), nullable=True)
    interests_json: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    diagnostic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diagnostic_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    diagnostic_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weak_points_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
