"""
Юнит-тесты юзкейсов пользовательских конспектов.

Проверяются три вещи, ради которых конспекты и переносились в юзкейсы: наружу
ходит DTO, а не доменная сущность; данные проверяются до записи; чужой конспект
не удаляется по чужому идентификатору.
"""

import pytest

from src.application.dto.documents import UserDocumentDTO, UserDocumentsPageDTO
from src.application.exceptions import InvalidDocumentDataError
from src.application.use_cases.documents import (
    AddUserDocumentUseCase,
    DeleteUserDocumentUseCase,
    ListUserDocumentsUseCase,
)
from src.domain.entities import UserDocument
from src.domain.value_objects import DocumentTitle, Timestamp, UserDocumentID, UserID
from tests.fixtures.fakes import FakeUnitOfWork, FakeUserDocumentRepository

LONG_CONTENT = (
    "Конспект про частицы: は маркирует тему предложения, が выделяет субъект, "
    "を показывает объект действия, а に указывает направление, место времени "
    "и адресата — без этого живой разбор не собрать целиком."
)


def make_document(document_id: int, user_id: int, content: str) -> UserDocument:
    """Собрать доменный конспект.

    Args:
        document_id: Идентификатор конспекта.
        user_id: Идентификатор владельца.
        content: Текст конспекта.

    Returns:
        Доменный конспект.
    """
    timestamp = Timestamp.now()
    return UserDocument(
        id=UserDocumentID(document_id),
        user_id=UserID(user_id),
        title=DocumentTitle(f"Конспект {document_id}"),
        content=content,
        created_at=timestamp,
    )


class TestListUserDocuments:
    """Группа тестов списка конспектов."""

    async def test_page_is_built_from_dtos_not_entities(self) -> None:
        """
        Тестируем: тип результата списка.
        Отдаём: два конспекта пользователя.
        Ожидаем: страницу с DTO-элементами, доменные сущности наружу не уходят.
        """
        repository = _repository_with_documents()
        use_case = ListUserDocumentsUseCase(_uow(repository))

        page = await use_case.execute(user_id=1)

        assert isinstance(page, UserDocumentsPageDTO)
        assert all(isinstance(item, UserDocumentDTO) for item in page.documents)

    async def test_page_exposes_only_owners_documents(self) -> None:
        """
        Тестируем: разграничение по владельцу.
        Отдаём: конспекты пользователей 1 и 2.
        Ожидаем: в странице только конспекты запрошенного пользователя.
        """
        repository = _repository_with_documents()
        use_case = ListUserDocumentsUseCase(_uow(repository))

        page = await use_case.execute(user_id=1)

        assert [item.title for item in page.documents] == ["Конспект 1", "Конспект 2"]

    async def test_full_text_is_not_exposed(self) -> None:
        """
        Тестируем: объём данных в списке.
        Отдаём: конспект с длинным текстом.
        Ожидаем: DTO содержит превью, а не весь текст целиком.
        """
        repository = _repository_with_documents()
        use_case = ListUserDocumentsUseCase(_uow(repository))

        page = await use_case.execute(user_id=1)

        document = page.documents[0]
        assert document.preview != LONG_CONTENT
        assert document.preview.endswith("...")
        assert "preview" in document.model_dump()
        assert "content" not in document.model_dump()

    async def test_character_count_sums_own_content(self) -> None:
        """
        Тестируем: суммарный объём текста.
        Отдаём: два своих конспекта и один чужой.
        Ожидаем: сумма символов только по своим конспектам.
        """
        repository = _repository_with_documents()
        use_case = ListUserDocumentsUseCase(_uow(repository))

        page = await use_case.execute(user_id=1)

        assert page.character_count == len(LONG_CONTENT) * 2


class TestAddUserDocument:
    """Группа тестов добавления конспекта."""

    async def test_valid_document_is_written_normalized(self) -> None:
        """
        Тестируем: запись корректных данных.
        Отдаём: заголовок с пробелами по краям и текст с хвостовым пробелом.
        Ожидаем: в репозиторий уходят очищенные значения.
        """
        repository = _empty_repository()
        use_case = AddUserDocumentUseCase(_uow(repository))

        await use_case.execute(user_id=1, title="  Кандзи  ", content=f"{LONG_CONTENT} ")

        assert repository.created == [(1, "Кандзи", LONG_CONTENT)]

    async def test_blank_title_is_rejected_before_write(self) -> None:
        """
        Тестируем: пустой заголовок.
        Отдаём: строку из пробелов.
        Ожидаем: ошибку данных конспекта и ни одной записи в репозитории.
        """
        repository = _empty_repository()
        use_case = AddUserDocumentUseCase(_uow(repository))

        with pytest.raises(InvalidDocumentDataError):
            await use_case.execute(user_id=1, title="   ", content=LONG_CONTENT)

        assert repository.created == []

    async def test_stub_content_is_rejected_before_write(self) -> None:
        """
        Тестируем: слишком короткий текст.
        Отдаём: пять символов вместо конспекта.
        Ожидаем: ошибку данных, репозиторий не тронут.
        """
        repository = _empty_repository()
        use_case = AddUserDocumentUseCase(_uow(repository))

        with pytest.raises(InvalidDocumentDataError):
            await use_case.execute(user_id=1, title="Тема", content="фука")

        assert repository.created == []


class TestDeleteUserDocument:
    """Группа тестов удаления конспекта."""

    async def test_owner_document_is_removed(self) -> None:
        """
        Тестируем: удаление собственного конспекта.
        Отдаём: идентификатор конспекта владельца.
        Ожидаем: True, конспект удалён из хранилища.
        """
        repository = _repository_with_documents()
        use_case = DeleteUserDocumentUseCase(_uow(repository))

        assert await use_case.execute(user_id=1, document_id=1) is True
        assert repository.deleted == [1]

    async def test_foreign_document_is_not_removed(self) -> None:
        """
        Тестируем: удаление чужого конспекта по угаданному идентификатору.
        Отдаём: идентификатор конспекта другого пользователя.
        Ожидаем: False и ни одного обращения к удалению.
        """
        repository = _repository_with_documents()
        use_case = DeleteUserDocumentUseCase(_uow(repository))

        assert await use_case.execute(user_id=1, document_id=3) is False
        assert repository.deleted == []

    async def test_missing_document_returns_false(self) -> None:
        """
        Тестируем: несуществующий идентификатор.
        Отдаём: документ 999.
        Ожидаем: False вместо исключения.
        """
        repository = _repository_with_documents()
        use_case = DeleteUserDocumentUseCase(_uow(repository))

        assert await use_case.execute(user_id=1, document_id=999) is False


def _repository_with_documents() -> FakeUserDocumentRepository:
    """Собрать репозиторий с двумя своими и одним чужим конспектом.

    Returns:
        Подмена репозитория документов.
    """
    return FakeUserDocumentRepository(
        [
            make_document(1, 1, LONG_CONTENT),
            make_document(2, 1, LONG_CONTENT),
            make_document(3, 2, "Чужой конспект, который нельзя трогать."),
        ]
    )


def _empty_repository() -> FakeUserDocumentRepository:
    """Собрать пустой репозиторий документов.

    Returns:
        Подмена репозитория документов без записей.
    """
    return FakeUserDocumentRepository([])


def _uow(repository: FakeUserDocumentRepository) -> FakeUnitOfWork:
    """Собрать unit of work с репозиторием документов.

    Args:
        repository: Подмена репозитория документов.

    Returns:
        Unit of Work поверх словаря репозиториев.
    """
    return FakeUnitOfWork({"user_document": repository})
