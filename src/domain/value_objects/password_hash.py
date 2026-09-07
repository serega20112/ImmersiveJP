from dataclasses import dataclass

from src.domain.exceptions import InvalidPasswordHashError


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Хеш пароля пользователя."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not str(self.value).strip():
            raise InvalidPasswordHashError(
                "Хеш пароля не может быть пустым",
                details={"field": "password_hash"},
            )

    def __str__(self) -> str:
        return self.value
