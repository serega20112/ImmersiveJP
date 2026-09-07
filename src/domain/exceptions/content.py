from .base import DomainError


class ContentDomainError(DomainError):
    """Базовая ошибка доменной области контента."""


class InvalidBatchNumberError(ContentDomainError):
    """Некорректный номер батча."""


class InvalidCardPositionError(ContentDomainError):
    """Некорректная позиция карточки."""


class CardAlreadyCompletedError(ContentDomainError):
    """Карточка уже отмечена как завершённая."""
