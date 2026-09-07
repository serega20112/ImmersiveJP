import logging
import time
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import text

from src.application.interfaces import DatabaseClient
from src.application.interfaces.exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseTransactionError,
)

logger = logging.getLogger(__name__)


class PostgresDatabaseClient(DatabaseClient):
    """
    Адаптер для работы с PostgreSQL через SQLAlchemy.

    Реализует интерфейс DatabaseClient, предоставляя низкоуровневые операции
    с базой данных.
    """

    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 20, max_overflow: int = 40):
        """
        Инициализация адаптера.

        Аргументы:
            database_url: строка подключения к БД (например, postgresql+asyncpg://...).
            echo: флаг для логирования SQL-запросов.
        """
        self._database_url = database_url
        self._echo = echo
        self._pool_size = pool_size
        self._max_overflow = max_overflow

        self._engine: AsyncEngine | None = None
        self.sessionmaker: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Создать движок SQLAlchemy и проверить соединение."""
        start_time = time.perf_counter()

        try:
            self._engine = create_async_engine(
                self._database_url, echo=self._echo, pool_size=self._pool_size, max_overflow=self._max_overflow
            )
            self.sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info("База данных подключена (%.0fms)", duration_ms)

        except Exception as e:
            logger.exception("Ошибка подключения к базе данных")
            raise DatabaseConnectionError(f"Не удалось подключиться к PostgreSQL: {e}") from e

    async def disconnect(self) -> None:
        """Закрыть движок и освободить ресурсы."""
        if self._engine:
            try:
                await self._engine.dispose()
                logger.info("База данных отключена")
            except Exception:
                logger.exception("Ошибка при отключении базы данных")
                raise
            finally:
                self._engine = None
                self.sessionmaker = None

    async def execute(self, query: str, params: Mapping[str, Any] | None = None) -> Any:
        """
        Выполнить запрос на запись (INSERT, UPDATE, DELETE).

        Возвращает объект результата (например, количество затронутых строк).
        """
        if not self._engine:
            raise DatabaseError("Соединение не установлено")

        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text(query), params or {})
                await conn.commit()
            return result

        except Exception:
            logger.exception("Ошибка выполнения SQL-запроса")
            raise

    async def fetch_one(self, query: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        """Получить одну запись из базы данных."""
        if not self._engine:
            raise DatabaseError("Соединение не установлено")

        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text(query), params or {})
                return result.fetchone()
        except Exception:
            logger.exception("Ошибка получения одной записи")
            raise

    async def fetch_all(self, query: str, params: Mapping[str, Any] | None = None) -> Sequence[Any]:
        """Получить несколько записей из базы данных."""
        if not self._engine:
            raise DatabaseError("Соединение не установлено")

        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text(query), params or {})
                return result.fetchall()
        except Exception:
            logger.exception("Ошибка получения списка записей")
            raise

    def transaction(self) -> AsyncIterator[AsyncConnection]:
        """
        Создать контекстный менеджер для транзакции.

        Возвращает менеджер, который при входе начинает транзакцию,
        а при выходе коммитит (если не было исключения) или откатывает.
        """
        if not self._engine:
            raise DatabaseTransactionError("Соединение не установлено")

        logger.info("Контекстный менеджер для транзакции создан")
        return self._engine.begin()

    async def health_check(self) -> bool:
        """Проверить состояние соединения с БД."""
        if not self._engine:
            return False

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            logger.exception("Health check БД не прошёл")
            return False
