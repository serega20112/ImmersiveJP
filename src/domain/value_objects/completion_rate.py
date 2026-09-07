from dataclasses import dataclass

from src.domain.exceptions import InvalidCompletionRateError


@dataclass(frozen=True, slots=True)
class CompletionRate:
    """Процент завершения трека (0–100)."""

    percentage: float

    def __post_init__(self) -> None:
        if not isinstance(self.percentage, (int, float)):
            raise InvalidCompletionRateError(
                f"Процент завершения должен быть числом: {self.percentage!r}",
                details={"value": self.percentage},
            )
        clamped = max(0.0, min(100.0, float(self.percentage)))
        object.__setattr__(self, "percentage", round(clamped, 1))

    def __str__(self) -> str:
        return f"{self.percentage}%"
