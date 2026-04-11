from __future__ import annotations

import json
import time
from typing import Any

from redis import asyncio as redis_asyncio
from redis.exceptions import RedisError


class KeyValueStore:
    def __init__(
        self,
        redis_url: str | None,
        namespace: str,
        required: bool = False,
    ):
        self._redis_url = redis_url
        self._namespace = namespace
        self._required = required
        self._redis = (
            redis_asyncio.from_url(redis_url, decode_responses=True)
            if redis_url
            else None
        )
        self._memory: dict[str, tuple[Any, float | None]] = {}

    def _make_key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    def _purge_memory_key(self, key: str) -> None:
        stored = self._memory.get(key)
        if stored is None:
            return
        _value, expires_at = stored
        if expires_at is not None and expires_at <= time.time():
            self._memory.pop(key, None)

    async def get_json(self, key: str) -> Any:
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                raw_value = await self._redis.get(namespaced)
                return json.loads(raw_value) if raw_value is not None else None
            except RedisError:
                if self._required:
                    raise
        self._purge_memory_key(namespaced)
        stored = self._memory.get(namespaced)
        return None if stored is None else stored[0]

    async def set_json(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = None,
    ) -> None:
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                await self._redis.set(namespaced, json.dumps(value), ex=expire_seconds)
                return
            except RedisError:
                if self._required:
                    raise
        expires_at = time.time() + expire_seconds if expire_seconds else None
        self._memory[namespaced] = (value, expires_at)

    async def delete(self, key: str) -> None:
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                await self._redis.delete(namespaced)
            except RedisError:
                if self._required:
                    raise
        self._memory.pop(namespaced, None)

    async def incr(self, key: str, expire_seconds: int) -> int:
        namespaced = self._make_key(key)
        if self._redis is not None:
            try:
                async with self._redis.pipeline(transaction=True) as pipeline:
                    pipeline.incr(namespaced)
                    pipeline.expire(namespaced, expire_seconds)
                    value, _ = await pipeline.execute()
                    return int(value)
            except RedisError:
                if self._required:
                    raise
        self._purge_memory_key(namespaced)
        value, expires_at = self._memory.get(namespaced, (0, None))
        next_value = int(value) + 1
        ttl = expires_at if expires_at is not None else time.time() + expire_seconds
        self._memory[namespaced] = (next_value, ttl)
        return next_value

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
