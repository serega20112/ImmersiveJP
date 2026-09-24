"""Проверить границы ошибок: домен, запись документа и деградация RAG.

Ни один из этих путей не покрыт тестами, а проверка «прогнал линтер и тесты»
тут ничего не доказывает: поведение меняется как раз там, где тестов нет. Скрипт
проверяет четыре обещания, данные аудитом архитектуры:

    1. доменная ошибка, дошедшая до HTTP, имеет обработчик и не уходит в catch-all;
    2. пустой заголовок документа отклоняется до записи в базу, а нормализуется — нет;
    3. RAG деградирует пустым списком только при отказе инфраструктуры;
    4. собственный дефект (ошибка в коде) не проглатывается и валится наружу.

Запуск:
    python -m scripts.check_error_boundaries
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from src.application.exceptions import ApplicationError, InvalidDocumentDataError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.exceptions import DatabaseError, InfrastructureError
from src.application.services.rag_service import RAGService
from src.application.use_cases.documents import AddUserDocumentUseCase
from src.domain.entities import UserDocument
from src.domain.exceptions import DomainError, UserAlreadyVerifiedError
from src.domain.value_objects import DocumentTitle, Timestamp, UserDocumentID, UserID
from src.infrastructures.external.embedding_client import EmbeddingError
from src.infrastructures.repositories.base_clients import SQLAlchemyUnitOfWork
from src.main import create_app
from src.presentation.http.exception_handlers import register_exception_handlers

failures: list[str] = []


def report(name: str, ok: bool, detail: str = "") -> None:
    """Зарегистрировать результат проверки.

    Args:
        name: Что проверялось.
        ok: Пройдена ли проверка.
        detail: Пояснение для вывода.
    """
    status = "ok  " if ok else "FAIL"
    print(f"{status} {name} {detail}".rstrip())
    if not ok:
        failures.append(name)


class _FakeDocumentRepository:
    """Подмена репозитория документов, сохраняющая аргументы вызова."""

    def __init__(self) -> None:
        self.created: list[tuple[int, Any, str]] = []
        self.documents: list[UserDocument] = []

    async def create(self, user_id: int, title: DocumentTitle, content: str) -> UserDocument:
        self.created.append((user_id, title, content))
        return _document(title)

    async def get_by_user(self, _user_id: int) -> list[UserDocument]:
        return self.documents


class _FakeUnitOfWork(UnitOfWork):
    """Минимальная подмена UoW с одним репозиторием.

    Наследуется от интерфейса, а не притворяется им: типизированные свойства
    репозиториев живут в самом интерфейсе, и подмена обязана получать их бесплатно,
    как и настоящий Unit of Work.
    """

    def __init__(self, repositories: dict[str, Any]) -> None:
        self._repositories = repositories

    async def __aenter__(self) -> _FakeUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None and exc_type not in (ApplicationError, DomainError):
            raise exc_val

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    def repository(self, name: str) -> Any:
        return self._repositories[name]


class _FakeEmbeddingClient:
    """Клиент эмбеддингов, выбрасывающий заданное исключение."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    async def embed(self, _texts: list[str]) -> list[list[float]]:
        raise self._error


def _document(title: DocumentTitle) -> UserDocument:
    """Собрать пользовательский документ.

    Args:
        title: Заголовок.

    Returns:
        Документ с фиксированным содержимым.
    """
    return UserDocument(
        id=UserDocumentID(1),
        user_id=UserID(1),
        title=title,
        content="Первый абзац про японский язык.",
        created_at=Timestamp.now(),
    )


async def check_domain_handler_registered() -> None:
    """Убедиться, что доменная ошибка имеет свой обработчик, а не catch-all."""
    app = create_app()
    register_exception_handlers(app)
    handler = app.exception_handlers.get(DomainError)
    report("доменный обработчик зарегистрирован", handler is not None)


def check_domain_error_maps_to_user_already_verified() -> None:
    """Убедиться, что конкретное доменное исключение входит в иерархию DomainError."""
    error = UserAlreadyVerifiedError("почта уже подтверждена")
    report(
        "UserAlreadyVerifiedError наследует DomainError",
        isinstance(error, DomainError),
    )


async def check_document_title_enforced() -> None:
    """Проверить, что заголовок и текст проверяются до записи, а не после."""
    repository = _FakeDocumentRepository()
    use_case = AddUserDocumentUseCase(_FakeUnitOfWork({"user_document": repository}))
    valid_content = "Конспект про частицы: は маркирует тему предложения."

    try:
        await use_case.execute(1, "   ", valid_content)
        report("пустой заголовок отклонён до записи", False, "исключение не поднято")
        return
    except InvalidDocumentDataError as error:
        report("пустой заголовок отклонён до записи", True, f"({error.message})")

    report("пустой заголовок не дошёл до репозитория", not repository.created)

    try:
        await use_case.execute(1, "Заголовок", " kurz ")
        report("обрывок текста отклонён до записи", False, "исключение не поднято")
    except InvalidDocumentDataError:
        report("обрывок текста отклонён до записи", True)

    await use_case.execute(1, "  Конспект  ", valid_content)
    stored_user_id, stored_title, stored_content = repository.created[0]
    report(
        "заголовок нормализуется перед записью",
        isinstance(stored_title, DocumentTitle) and stored_title.value == "Конспект",
        f"(получено {stored_title!r})",
    )
    report(
        "текст сохраняется очищенным",
        stored_content == valid_content and stored_user_id == 1,
        f"(получено {stored_content!r})",
    )


async def check_rag_degrades_on_infrastructure_error() -> None:
    """При отказе эмбеддингов RAG обязан вернуть пустой список, не упав."""
    document_title = DocumentTitle("Тема")
    repository = _FakeDocumentRepository()
    repository.documents = [_document(document_title)]
    uow = _FakeUnitOfWork({"user_document": repository})
    service = RAGService(lambda: uow, _FakeEmbeddingClient(EmbeddingError("сервис лежит")))

    results = await service.query(1, "частица wa")
    report("отказ эмбеддингов деградирует пустым списком", results == [], f"(получено {results!r})")


async def check_rag_propagates_programming_error() -> None:
    """Собственный дефект не должен превращаться в «нет результатов»."""
    repository = _FakeDocumentRepository()
    repository.documents = [_document(DocumentTitle("Тема"))]
    uow = _FakeUnitOfWork({"user_document": repository})
    service = RAGService(lambda: uow, _FakeEmbeddingClient(AttributeError("опечатка в коде")))

    try:
        await service.query(1, "частица wa")
    except AttributeError:
        report("ошибка программы не проглочена", True)
        return
    except Exception as error:
        report("ошибка программы не проглочена", False, f"(поймано {type(error).__name__})")
        return
    report("ошибка программы не проглочена", False, "(query вернул список вместо падения)")


async def check_unit_of_work_translates_sqlalchemy_error() -> None:
    """Ошибка SQLAlchemy обязана выходить DatabaseError, а не чужим типом."""
    uow = SQLAlchemyUnitOfWork(lambda: None)

    try:
        async with uow:
            raise SQLAlchemyError("соединение потеряно")
    except DatabaseError:
        report("SQLAlchemyError переведён в DatabaseError", True)
        return
    except Exception as error:
        report(
            "SQLAlchemyError переведён в DatabaseError",
            False,
            f"(поймано {type(error).__name__})",
        )
        return
    report("SQLAlchemyError переведён в DatabaseError", False, "(ошибка не поднялась)")


def check_embedding_error_is_infrastructure() -> None:
    """Ошибка эмбеддингов должна относиться к инфраструктурным, а не к RuntimeError."""
    report(
        "EmbeddingError наследует InfrastructureError",
        issubclass(EmbeddingError, InfrastructureError),
    )


async def main() -> int:
    """Прогнать все проверки границ ошибок.

    Returns:
        Код завершения: 0 — границы держатся, 1 — есть провалы.
    """
    await check_domain_handler_registered()
    check_domain_error_maps_to_user_already_verified()
    check_embedding_error_is_infrastructure()
    await check_document_title_enforced()
    await check_rag_degrades_on_infrastructure_error()
    await check_rag_propagates_programming_error()
    await check_unit_of_work_translates_sqlalchemy_error()

    if failures:
        print(f"RESULT: {len(failures)} ПРОБЛЕМ: {', '.join(failures)}")
        return 1
    print("RESULT: ALL ERROR BOUNDARIES HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
