import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidEmailError


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = str(self.value or "").strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise InvalidEmailError(
                f"Некорректный формат email: {self.value!r}",
                details={"field": "email", "value": self.value},
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
