"""Подмены инфраструктурных зависимостей для юнит-тестов.

FakeUnitOfWork реализует порт UnitOfWork на словаре репозиториев,
FakeUserRepository хранит пользователей в памяти и фиксирует вызовы.
"""

from __future__ import annotations

from src.application.interfaces import UnitOfWork
from src.domain.aggregates.user import User
from src.domain.entities import UserDocument
from src.domain.value_objects import DocumentTitle, Timestamp, UserDocumentID, UserID


class FakePasswordService:
    """Подмена PasswordService: детерминированный хеш без bcrypt."""

    def __init__(self) -> None:
        """Инициализировать журнал хешированных паролей."""
        self.hashed: list[str] = []

    async def hash_password(self, password: str) -> str:
        """Вернуть псевдо-хеш вида ``hashed:<password>``.

        Args:
            password: Исходный пароль.

        Returns:
            Детерминированная строка хеша.
        """
        self.hashed.append(password)
        return f"hashed:{password}"

    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Сравнить пароль с псевдо-хешем.

        Args:
            password: Исходный пароль.
            password_hash: Ранее выданный псевдо-хеш.

        Returns:
            True, если хеш соответствует паролю.
        """
        return password_hash == f"hashed:{password}"


class FakeUserRepository:
    """In-memory репозиторий пользователей с записью вызовов записи."""

    def __init__(self, users: list[User] | None = None) -> None:
        """Инициализировать хранилище существующими пользователями.

        Args:
            users: Пользователи, доступные для поиска до начала теста.
        """
        self._by_email = {user.email.value: user for user in users or [] if user.id is not None}
        self._by_id = {user.id: user for user in users or [] if user.id is not None}
        self._next_id = max((user.id for user in users or [] if user.id is not None), default=0) + 1
        self.added: list[User] = []
        self.saved: list[User] = []

    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email.

        Args:
            email: Нормализованный адрес электронной почты.

        Returns:
            Пользователь или None, если не найден.
        """
        return self._by_email.get(email)

    async def get_by_id(self, user_id: int) -> User | None:
        """Найти пользователя по идентификатору.

        Args:
            user_id: Числовой идентификатор пользователя.

        Returns:
            Пользователь или None, если не найден.
        """
        return self._by_id.get(user_id)

    async def add(self, user: User) -> User:
        """Сохранить нового пользователя, назначив ему следующий id.

        Args:
            user: Новый доменный пользователь без id.

        Returns:
            Тот же объект с назначенным идентификатором.
        """
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
        self._by_email[user.email.value] = user
        self._by_id[user.id] = user
        self.added.append(user)
        return user

    async def save(self, user: User) -> User:
        """Обновить существующего пользователя.

        Args:
            user: Пользователь с изменённым состоянием.

        Returns:
            Тот же объект пользователя.
        """
        self.saved.append(user)
        return user


class StubUseCase:
    """Подмена use case-объекта: записывает вызовы и отдаёт заданный результат."""

    def __init__(self, result: object = None) -> None:
        """Инициализировать заглушку с предопределённым результатом.

        Args:
            result: Значение, которое вернёт ``execute``.
        """
        self.result = result
        self.calls: list[tuple[object, ...]] = []

    async def execute(self, *args: object) -> object:
        """Записать аргументы вызова и вернуть заданный результат.

        Args:
            *args: Аргументы, переданные сервисом-фасадом.

        Returns:
            Значение, переданное в конструктор.
        """
        self.calls.append(args)
        return self.result


class FakeKeyValueStore:
    """In-memory реализация порта KeyValueStore для юнит-тестов."""

    def __init__(self, values: dict[str, object] | None = None) -> None:
        """Инициализировать хранилище начальными значениями.

        Args:
            values: Ключи и значения, доступные до начала теста.
        """
        self.values: dict[str, object] = dict(values or {})
        self.expirations: dict[str, int | None] = {}
        self.deleted: list[str] = []
        self.increments: list[tuple[str, int]] = []

    async def get_json(self, key: str) -> object:
        """Получить значение по ключу.

        Args:
            key: Ключ хранилища.

        Returns:
            Сохранённое значение или None.
        """
        return self.values.get(key)

    async def set_json(self, key: str, value: object, expire_seconds: int | None = None) -> None:
        """Сохранить значение и запомнить TTL.

        Args:
            key: Ключ хранилища.
            value: Сохраняемое значение.
            expire_seconds: Время жизни ключа.
        """
        self.values[key] = value
        self.expirations[key] = expire_seconds

    async def delete(self, key: str) -> None:
        """Удалить ключ из хранилища.

        Args:
            key: Ключ хранилища.
        """
        self.deleted.append(key)
        self.values.pop(key, None)

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Инкрементировать счётчик по ключу.

        Args:
            key: Ключ счётчика.
            expire_seconds: Время жизни ключа.

        Returns:
            Новое значение счётчика.
        """
        self.increments.append((key, expire_seconds))
        current = int(self.values.get(key, 0)) + 1
        self.values[key] = current
        self.expirations[key] = expire_seconds
        return current

    async def close(self) -> None:
        """Закрыть хранилище (для подмены никаких действий не требуется)."""
        return None


class FakeEmbeddingClient:
    """Подмена EmbeddingClient: вектора берутся из словаря текст -> вектор."""

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        """Инициализировать клиент картой векторов.

        Args:
            vectors: Соответствие текста его вектору эмбеддинга.
        """
        self.vectors = vectors
        self.requested: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Вернуть векторы для переданных текстов.

        Args:
            texts: Тексты для векторизации.

        Returns:
            Список векторов в порядке переданных текстов.

        Raises:
            KeyError: Если для текста не задан вектор (имитация сбоя).
        """
        self.requested.append(list(texts))
        return [self.vectors[text] for text in texts]


class FakeUserDocumentRepository:
    """In-memory репозиторий документов пользователя."""

    def __init__(self, documents: list[UserDocument] | None = None) -> None:
        """Инициализировать хранилище документами.

        Args:
            documents: Документы, доступные до начала теста.
        """
        self.documents = list(documents or [])
        self.created: list[tuple[int, str, str]] = []
        self.deleted: list[int] = []

    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Вернуть документы конкретного пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Список документов пользователя.
        """
        return [doc for doc in self.documents if int(doc.user_id) == user_id]

    async def get(self, doc_id: int) -> UserDocument | None:
        """Найти документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.

        Returns:
            Документ или None, если не найден.
        """
        for document in self.documents:
            if document.id is not None and int(document.id) == doc_id:
                return document
        return None

    async def create(self, user_id: int, title: DocumentTitle, content: str) -> UserDocument:
        """Создать документ и добавить его в хранилище.

        Заголовок приходит проверенным value object'ом — как требует порт,
        а не строкой, которую репозиторий валидирует сам.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок документа.
            content: Текст документа.

        Returns:
            Созданный документ.
        """
        self.created.append((user_id, str(title), content))
        document = UserDocument(
            id=UserDocumentID(len(self.documents) + 1),
            user_id=UserID(user_id),
            title=title,
            content=content,
            created_at=Timestamp.now(),
        )
        self.documents.append(document)
        return document

    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.
        """
        self.deleted.append(doc_id)
        self.documents = [
            document
            for document in self.documents
            if not (document.id is not None and int(document.id) == doc_id)
        ]


class FakeUnitOfWork(UnitOfWork):
    """Unit of Work поверх словаря репозиториев, без реальной транзакции."""

    def __init__(self, repositories: dict[str, object] | None = None) -> None:
        """Инициализировать unit of work набором репозиториев.

        Args:
            repositories: Соответствие имени репозитория его реализации.
        """
        self._repositories = repositories or {}
        self.entered = 0
        self.committed = 0
        self.rolled_back = 0

    async def __aenter__(self) -> FakeUnitOfWork:
        """Открыть транзакционную границу.

        Returns:
            Этот же объект unit of work.
        """
        self.entered += 1
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Закрыть транзакционную границу без дополнительных действий."""
        return None

    async def commit(self) -> None:
        """Зафиксировать транзакцию (только счётчик вызовов)."""
        self.committed += 1

    async def rollback(self) -> None:
        """Откатить транзакцию (только счётчик вызовов)."""
        self.rolled_back += 1

    def repository(self, name: str) -> object:
        """Вернуть репозиторий по имени.

        Args:
            name: Имя репозитория, например "user".

        Returns:
            Реализация репозитория, переданная при создании.
        """
        return self._repositories[name]
