from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.infrastructure.files.database import Base
from src.backend.infrastructure.models.timestamp import TimestampMixin


class UserDocument(TimestampMixin, Base):
    """Таблица пользовательских конспектов.
    Хранит заголовок и текстовое содержимое, привязанное к конкретному пользователю.
    """

    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="documents")
