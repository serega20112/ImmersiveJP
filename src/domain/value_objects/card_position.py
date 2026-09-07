from dataclasses import dataclass

from src.domain.exceptions import InvalidCardPositionError


@dataclass(frozen=True, slots=True)
class CardPosition:
    """Позиция карточки в батче."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 1:
            raise InvalidCardPositionError(
                f"Позиция карточки должна быть положительным целым числом: {self.value!r}",
                details={"value": self.value},
            )

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, bool):
            return NotImplemented
        if isinstance(other, int):
            return self.value == other
        if isinstance(other, CardPosition):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, CardPosition):
            return self.value < other.value
        if isinstance(other, int) and not isinstance(other, bool):
            return self.value < other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return str(self.value)
