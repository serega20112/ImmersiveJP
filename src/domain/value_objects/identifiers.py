from src.domain.exceptions import InvalidIDValueError


class IntID:
    """Базовый класс для целочисленных идентификаторов с валидацией."""

    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise InvalidIDValueError(
                f"Некорректный ID для {self.__class__.__name__}: {value}",
                details={"field": self.__class__.__name__, "value": value},
            )
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def __int__(self) -> int:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, bool):
            return NotImplemented
        if isinstance(other, int):
            return self._value == other
        if not isinstance(other, IntID):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


class UserID(IntID):
    """Идентификатор пользователя."""


class LearningCardID(IntID):
    """Идентификатор учебной карточки."""


class UserDocumentID(IntID):
    """Идентификатор пользовательского документа."""
