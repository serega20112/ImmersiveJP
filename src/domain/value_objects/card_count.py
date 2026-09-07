from dataclasses import dataclass

from src.domain.exceptions import InvalidCardCountError


@dataclass(frozen=True, slots=True)
class CardCount:
    """Количество карточек."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 0:
            raise InvalidCardCountError(
                f"Количество карточек не может быть отрицательным: {self.value!r}",
                details={"value": self.value},
            )

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)
