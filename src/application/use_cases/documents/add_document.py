"""Юзкейс добавления пользовательского конспекта."""

from __future__ import annotations

from src.application.exceptions import InvalidDocumentDataError
from src.application.interfaces import UnitOfWork
from src.domain.exceptions import InvalidDocumentTitleError
from src.domain.value_objects import DocumentTitle

MIN_CONTENT_LENGTH = 20


class AddUserDocumentUseCase:
    """Сохранить новый конспект пользователя."""

    def __init__(self, uow: UnitOfWork):
        """Инициализировать юзкейс добавления конспекта.

        Args:
            uow: Единица работы с базой.
        """
        self._uow = uow

    async def execute(self, user_id: int, title: str, content: str) -> None:
        """Проверить данные и сохранить конспект.

        Заголовок собирается в value object до похода в репозиторий. Иначе
        инвариант «не пустой» не действует вовсе: строка уходит в базу, а
        обратно её прочитать нельзя — разбор в DocumentTitle бросает исключение
        на чтении. Пропущенная проверка превращалась в отложенный 500 там, где
        пользователь просто отправил пустую форму.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок конспекта.
            content: Текст конспекта.

        Raises:
            InvalidDocumentDataError: Если домен отклонил заголовок или текст пуст.
        """
        try:
            document_title = DocumentTitle(title)
        except InvalidDocumentTitleError as error:
            raise InvalidDocumentDataError(str(error)) from error

        cleaned_content = str(content or "").strip()
        if len(cleaned_content) < MIN_CONTENT_LENGTH:
            raise InvalidDocumentDataError(
                f"Конспект слишком короткий: минимум {MIN_CONTENT_LENGTH} символов"
            )

        async with self._uow as uow:
            await uow.user_documents.create(user_id, document_title, cleaned_content)
