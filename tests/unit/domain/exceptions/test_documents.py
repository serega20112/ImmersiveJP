"""
Юнит-тесты ошибок доменной области документов.

Проверяется: наследование DocumentDomainError и сохранение сообщения.
"""

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.documents import DocumentDomainError, InvalidDocumentTitleError


class TestDocumentDomainErrors:
    """Группа тестов ошибок доменной области документов."""

    def test_inherits_document_and_domain_error(self) -> None:
        """
        Тестируем: иерархию ошибки заголовка документа.
        Отдаём: ошибку с сообщением.
        Ожидаем: наследует DocumentDomainError и DomainError.
        """
        error = InvalidDocumentTitleError("Пустой заголовок")

        assert isinstance(error, DocumentDomainError)
        assert isinstance(error, DomainError)
        assert error.message == "Пустой заголовок"
