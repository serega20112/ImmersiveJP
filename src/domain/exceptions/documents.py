from .base import DomainError


class DocumentDomainError(DomainError):
    """Базовая ошибка доменной области документов."""


class InvalidDocumentTitleError(DocumentDomainError):
    """Некорректный заголовок документа."""
