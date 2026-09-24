"""Юзкейс списка пользовательских конспектов."""

from __future__ import annotations

from src.application.dto.documents import UserDocumentsPageDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.mappers import to_user_document_dto


class ListUserDocumentsUseCase:
    """Вернуть список конспектов пользователя."""

    def __init__(self, uow: UnitOfWork):
        """Инициализировать юзкейс списка конспектов.

        Args:
            uow: Единица работы с базой.
        """
        self._uow = uow

    async def execute(self, user_id: int) -> UserDocumentsPageDTO:
        """Собрать страницу списка конспектов.

        Наружу отдаётся DTO, а не доменные сущности: список идёт в шаблон, и
        сущность протаскала бы в презентацию и свои value objects, и свои
        внутренности вроде полного текста каждого документа.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Страницу списка конспектов.
        """
        async with self._uow as uow:
            documents = await uow.user_documents.get_by_user(user_id)
        return UserDocumentsPageDTO(
            documents=[to_user_document_dto(document) for document in documents],
            character_count=sum(len(document.content) for document in documents),
        )
