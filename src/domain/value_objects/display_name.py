from dataclasses import dataclass

from src.domain.exceptions import InvalidDisplayNameError

_MIN_LENGTH = 1
_MAX_LENGTH = 100


@dataclass(frozen=True, slots=True)
class DisplayName:
    """Отображаемое имя пользователя."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidDisplayNameError(
                "Отображаемое имя должно быть строкой",
                details={"value": self.value},
            )
        normalized = self.value.strip()
        if len(normalized) < _MIN_LENGTH:
            raise InvalidDisplayNameError(
                "Отображаемое имя не может быть пустым",
                details={"value": self.value},
            )
        if len(normalized) > _MAX_LENGTH:
            raise InvalidDisplayNameError(
                f"Отображаемое имя не может быть длиннее {_MAX_LENGTH} символов",
                details={"value": self.value, "max_length": _MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
