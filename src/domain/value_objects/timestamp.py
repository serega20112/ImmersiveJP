from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import InvalidTimestampValueError


@dataclass(frozen=True, slots=True)
class Timestamp:
    """Момент времени с обязательным часовым поясом, нормализованный в UTC."""

    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise InvalidTimestampValueError(
                "Timestamp должен содержать datetime",
                details={"value": self.value},
            )
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise InvalidTimestampValueError(
                "Timestamp должен содержать часовой пояс",
                details={"value": self.value},
            )
        object.__setattr__(self, "value", self.value.astimezone(UTC))

    @classmethod
    def now(cls) -> Self:
        """Фиксирует текущий момент времени в UTC."""
        return cls(datetime.now(UTC))

    def refresh(self) -> Self:
        """Фиксирует время следующего изменения, не позволяя времени идти назад."""
        timestamp = type(self).now()
        if timestamp.value < self.value:
            raise InvalidTimestampValueError(
                "Время изменения не может быть раньше предыдущего значения",
                details={"current": str(self), "new": str(timestamp)},
            )
        return timestamp

    def __str__(self) -> str:
        return self.value.isoformat()
