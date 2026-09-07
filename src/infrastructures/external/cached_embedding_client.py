"""Клиент эмбеддингов с кэшированием в key-value хранилище."""

from __future__ import annotations

from hashlib import sha256

from src.application.interfaces.clients import EmbeddingClient, KeyValueStore
from src.config.settings import settings


class CachedEmbeddingClient:
    """Декоратор EmbeddingClient: кэширует векторы по хешу текста."""

    def __init__(self, embed_client: EmbeddingClient, cache: KeyValueStore):
        """Инициализировать кэширующий клиент.

        Args:
            embed_client: Базовый клиент эмбеддингов.
            cache: Key-value хранилище для кэша векторов.
        """
        self._embed_client = embed_client
        self._cache = cache

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Вернуть векторы эмбеддингов, докомпоновывая недостающие из клиента.

        Args:
            texts: Тексты для векторизации.

        Returns:
            Список векторов эмбеддингов в порядке входных текстов.
        """
        keys = [
            f"{_cache_prefix()}:{_text_hash(text)}"
            for text in texts
        ]
        cached = [await self._cache.get_json(key) for key in keys]
        missing = [index for index, value in enumerate(cached) if not isinstance(value, list)]
        if missing:
            fresh = await self._embed_client.embed([texts[index] for index in missing])
            for index, vector in zip(missing, fresh, strict=True):
                cached[index] = vector
                await self._cache.set_json(
                    keys[index],
                    vector,
                    expire_seconds=settings.rag.rag_embedding_cache_ttl_seconds,
                )
        return [list(value) for value in cached]  # type: ignore[arg-type]


def _cache_prefix() -> str:
    """Префикс ключей кэша эмбеддингов."""
    return "rag:emb:v1"


def _text_hash(text: str) -> str:
    """Хеш текста с учётом модели эмбеддингов."""
    model = settings.llm.embedding_model
    return sha256(f"{model}:{text}".encode()).hexdigest()
