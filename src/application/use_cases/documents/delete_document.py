"""Юзкейс удаления пользовательского конспекта."""

from __future__ import annotations

from src.application.interfaces import UnitOfWork


class DeleteUserDocumentUseCase:
    """Удалить конспект пользователя по идентификатору."""

    def __init__(self, uow: UnitOfWork):
        """Инициализировать юзкейс удаления конспекта.

        Args:
            uow: Единица работы с базой.
        """
        self._uow = uow

    async def execute(self, user_id: int, document_id: int) -> bool:
        """Удалить конспект, если он принадлежит этому пользователю.

        Проверка владельца обязательна до удаления: без неё достаточно было
        угадать идентификатор чужого конспекта, чтобы его стереть.

        Args:
            user_id: Идентификатор пользователя.
            document_id: Идентификатор конспекта.

        Returns:
            True, если конспект найден и удалён.
        """
        async with self._uow as uow:
            document = await uow.user_documents.get(document_id)
            if document is None or int(document.user_id) != user_id:
                return False
            await uow.user_documents.delete(document_id)
        return True
