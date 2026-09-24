"""Сервис пользовательских конспектов."""

from __future__ import annotations

from src.application.dto.documents import UserDocumentsPageDTO
from src.application.use_cases.documents import (
    AddUserDocumentUseCase,
    DeleteUserDocumentUseCase,
    ListUserDocumentsUseCase,
)


class DocumentService:
    """Фасад конспектов для презентационного слоя.

    Сам ничего не знает про базу и про домен: только разбирает вызов роута в
    конкретный юзкейс. Так держится один ответ на вопрос «где живёт логика» —
    в юзкейсе, а сервис остаётся точкой входа для HTTP-слоя.
    """

    def __init__(
        self,
        list_documents_use_case: ListUserDocumentsUseCase,
        add_document_use_case: AddUserDocumentUseCase,
        delete_document_use_case: DeleteUserDocumentUseCase,
    ):
        """Инициализировать сервис конспектов.

        Args:
            list_documents_use_case: Юзкейс списка конспектов.
            add_document_use_case: Юзкейс добавления конспекта.
            delete_document_use_case: Юзкейс удаления конспекта.
        """
        self._list_documents_use_case = list_documents_use_case
        self._add_document_use_case = add_document_use_case
        self._delete_document_use_case = delete_document_use_case

    async def list_documents(self, user_id: int) -> UserDocumentsPageDTO:
        """Вернуть страницу списка конспектов пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Страницу списка конспектов.
        """
        return await self._list_documents_use_case.execute(user_id)

    async def add_document(self, user_id: int, title: str, content: str) -> None:
        """Сохранить новый конспект пользователя.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок конспекта.
            content: Текст конспекта.

        Raises:
            InvalidDocumentDataError: Если домен отклонил данные конспекта.
        """
        await self._add_document_use_case.execute(user_id, title, content)

    async def delete_document(self, user_id: int, doc_id: int) -> bool:
        """Удалить конспект пользователя, если он ему принадлежит.

        Args:
            user_id: Идентификатор пользователя.
            doc_id: Идентификатор конспекта.

        Returns:
            True, если конспект найден и удалён.
        """
        return await self._delete_document_use_case.execute(user_id, doc_id)
