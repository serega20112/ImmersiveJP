"""Фабрика агрегата User и его публичного DTO-представления.

Простая фабрика без factory_boy (зависимость в проект не добавлялась):
метод build() возвращает валидный доменный объект, аргументы позволяют
переопределить отдельные поля.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.application.dto.auth import UserViewDTO
from src.domain.aggregates.user import User
from src.domain.value_objects import DisplayName, Email, PasswordHash, Timestamp


@dataclass
class UserFactory:
    """Строитель валидного агрегата User с предсказуемыми значениями по умолчанию."""

    email: str = "user@example.com"
    password_hash: str = "hashed-password"
    display_name: str = "Сергей"
    is_email_verified: bool = False
    onboarding_completed: bool = False
    user_id: int | None = None
    interests: list[str] = field(default_factory=list)

    def build(self, **overrides: object) -> User:
        """Собрать агрегат User с переопределением отдельных полей.

        Args:
            **overrides: Поля фабрики (email, user_id, is_email_verified и т.д.),
                переопределяемые для конкретного теста.

        Returns:
            Валидный доменный пользователь с заполненными value objects.
        """
        base = {
            "email": self.email,
            "password_hash": self.password_hash,
            "display_name": self.display_name,
            "is_email_verified": self.is_email_verified,
            "onboarding_completed": self.onboarding_completed,
            "user_id": self.user_id,
            "interests": list(self.interests),
        }
        base.update(overrides)

        timestamp = Timestamp.now()
        return User(
            id=base["user_id"],
            email=Email(str(base["email"])),
            password_hash=PasswordHash(str(base["password_hash"])),
            display_name=DisplayName(str(base["display_name"])),
            created_at=timestamp,
            updated_at=timestamp,
            is_email_verified=bool(base["is_email_verified"]),
            onboarding_completed=bool(base["onboarding_completed"]),
            interests=list(base["interests"]),
        )

    def build_view(self) -> UserViewDTO:
        """Собрать публичное DTO-представление пользователя.

        Returns:
            UserViewDTO, согласованный с текущими значениями фабрики.
        """
        return UserViewDTO(
            id=self.user_id or 1,
            email=self.email,
            display_name=self.display_name,
            is_email_verified=self.is_email_verified,
            onboarding_completed=self.onboarding_completed,
            interests=list(self.interests),
        )
