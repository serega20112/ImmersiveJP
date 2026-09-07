from dataclasses import dataclass

from src.domain.exceptions import InvalidDocumentTitleError


@dataclass(frozen=True, slots=True)
class DocumentTitle:
    """Заголовок пользовательского документа."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidDocumentTitleError(
                "Заголовок документа должен быть строкой",
                details={"value": self.value},
            )
        normalized = self.value.strip()
        if not normalized:
            raise InvalidDocumentTitleError(
                "Заголовок документа не может быть пустым",
                details={"value": self.value},
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
