"""Сервис управления пользовательскими документами."""

from __future__ import annotations

from src.application.exceptions import InvalidDocumentDataError
from src.application.interfaces import UnitOfWork
from src.domain.entities import UserDocument
from src.domain.exceptions import InvalidDocumentTitleError
from src.domain.value_objects import DocumentTitle


class DocumentService:
    """Инкапсулирует работу с документами пользователя через UoW."""

    def __init__(self, uow: UnitOfWork):
        """Инициализировать сервис документов.

        Args:
            uow: Unit of Work для транзакционной работы с БД.
        """
        self._uow = uow

    async def list_documents(self, user_id: int) -> list[UserDocument]:
        """Получить все документы пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Список документов пользователя.
        """
        async with self._uow as uow:
            doc_repository = uow.repository("user_document")
            return await doc_repository.get_by_user(user_id)

    async def add_document(self, user_id: int, title: str, content: str) -> None:
        """Сохранить новый документ пользователя.

        Заголовок собирается в value object до похода в репозиторий. Иначе
        инвариант «не пустой» не действует вовсе: строка уходит в базу, а
        обратно её прочитать нельзя — разбор в DocumentTitle бросает исключение
        на чтении. Пропущенная проверка превращалась в отложенный 500 там, где
        пользователь просто отправил пустую форму.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок документа.
            content: Текст документа.

        Raises:
            InvalidDocumentDataError: Если домен отклонил заголовок.
        """
        try:
            document_title = DocumentTitle(title)
        except InvalidDocumentTitleError as error:
            raise InvalidDocumentDataError(str(error)) from error
        async with self._uow as uow:
            doc_repository = uow.repository("user_document")
            await doc_repository.create(user_id, document_title, content)

    async def delete_document(self, user_id: int, doc_id: int) -> bool:
        """Удалить документ пользователя, если он ему принадлежит.

        Args:
            user_id: Идентификатор пользователя.
            doc_id: Идентификатор документа.

        Returns:
            True, если документ найден и удалён.
        """
        async with self._uow as uow:
            doc_repository = uow.repository("user_document")
            document = await doc_repository.get(doc_id)
            if document is None or document.user_id != user_id:
                return False
            await doc_repository.delete(doc_id)
            return True
