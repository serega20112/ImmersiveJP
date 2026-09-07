"""Key-value хранилище поверх Redis с in-memory фолбэком."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from redis import asyncio as redis_asyncio
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

_MEMORY_MAX_ENTRIES = 10_000


class KeyValueStore:
    """Хранилище JSON-значений: Redis, при недоступности — память процесса.

    In-memory фолбэк защищён блокировкой, автоматически очищает
    истёкшие записи и ограничен по размеру.
    """

    def __init__(
        self,
        redis_url: str | None,
        namespace: str,
        required: bool = False,
    ):
        """Инициализировать хранилище.

        Args:
            redis_url: URL подключения к Redis или None для memory-only.
            namespace: Префикс ключей.
            required: Строго ли требовать доступность Redis.
        """
        self._redis_url = redis_url
        self._namespace = namespace
        self._required = required
        self._redis = (
            redis_asyncio.from_url(redis_url, decode_responses=True) if redis_url else None
        )
        self._memory: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()
        self._last_purge_at = 0.0

    def _make_key(self, key: str) -> str:
        """Собрать полный ключ с namespace."""
        return f"{self._namespace}:{key}"

    async def _purge_expired(self) -> None:
        """Удалить истёкшие записи из памяти и ограничить её размер."""
        now = time.time()
        if now - self._last_purge_at < 60:
            return
        self._last_purge_at = now
        expired = [
            key
            for key, (_value, expires_at) in self._memory.items()
            if expires_at is not None and expires_at <= now
        ]
        for key in expired:
            self._memory.pop(key, None)
        if len(self._memory) > _MEMORY_MAX_ENTRIES:
            overflow = sorted(
                self._memory.items(),
                key=lambda item: item[1][1] or float("inf"),
            )
            for key, _stored in overflow[: len(self._memory) - _MEMORY_MAX_ENTRIES]:
                self._memory.pop(key, None)

    async def _memory_get(self, key: str) -> Any | None:
        """Потокобезопасно прочитать значение из памяти с проверкой TTL."""
        async with self._lock:
            await self._purge_expired()
            stored = self._memory.get(key)
            return None if stored is None else stored[0]

    async def _memory_set(self, key: str, value: Any, expires_at: float | None) -> None:
        """Потокобезопасно записать значение в память."""
        async with self._lock:
            self._memory[key] = (value, expires_at)

    async def _memory_delete(self, key: str) -> None:
        """Потокобезопасно удалить значение из памяти."""
        async with self._lock:
            self._memory.pop(key, None)

    async def _memory_incr(self, key: str, expire_seconds: int) -> int:
        """Потокобезопасно инкрементировать счётчик в памяти."""
        async with self._lock:
            await self._purge_expired()
            value, expires_at = self._memory.get(key, (0, None))
            next_value = int(value) + 1
            ttl = expires_at if expires_at is not None else time.time() + expire_seconds
            self._memory[key] = (next_value, ttl)
            return next_value

    def _log_redis_fallback(self, operation: str, error: RedisError) -> None:
        """Залогировать деградацию Redis до in-memory фолбэка."""
        logger.warning(
            "Redis unavailable, falling back to in-memory store",
            extra={
                "event": "cache.redis_fallback",
                "extra_fields": {
                    "operation": operation,
                    "required": self._required,
                    "error_type": type(error).__name__,
                },
            },
        )

    async def get_json(self, key: str) -> Any:
        """Получить JSON-значение по ключу.

        Args:
            key: Ключ без namespace.

        Returns:
            Значение или None, если ключ отсутствует.
        """
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                raw_value = await self._redis.get(namespaced)
                return json.loads(raw_value) if raw_value is not None else None
            except RedisError as error:
                if self._required:
                    raise
                self._log_redis_fallback("get", error)
        return await self._memory_get(namespaced)

    async def set_json(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = None,
    ) -> None:
        """Сохранить JSON-значение с опциональным TTL.

        Args:
            key: Ключ без namespace.
            value: Значение для сохранения.
            expire_seconds: Время жизни записи в секундах.
        """
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                await self._redis.set(namespaced, json.dumps(value), ex=expire_seconds)
                return
            except RedisError as error:
                if self._required:
                    raise
                self._log_redis_fallback("set", error)
        expires_at = time.time() + expire_seconds if expire_seconds else None
        await self._memory_set(namespaced, value, expires_at)

    async def delete(self, key: str) -> None:
        """Удалить ключ.

        Args:
            key: Ключ без namespace.
        """
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                await self._redis.delete(namespaced)
            except RedisError as error:
                if self._required:
                    raise
                self._log_redis_fallback("delete", error)
        await self._memory_delete(namespaced)

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Инкрементировать счётчик и задать TTL.

        Args:
            key: Ключ без namespace.
            expire_seconds: Время жизни счётчика в секундах.

        Returns:
            Новое значение счётчика.
        """
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                async with self._redis.pipeline(transaction=True) as pipeline:
                    pipeline.incr(namespaced)
                    pipeline.expire(namespaced, expire_seconds)
                    value, _ = await pipeline.execute()
                    return int(value)
            except RedisError as error:
                if self._required:
                    raise
                self._log_redis_fallback("incr", error)
        return await self._memory_incr(namespaced, expire_seconds)

    async def close(self) -> None:
        """Закрыть соединение с Redis."""
        if self._redis is not None:
            await self._redis.aclose()
