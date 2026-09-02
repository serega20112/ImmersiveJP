"""Сервис RAG: поиск релевантных фрагментов в документах пользователя.

Pipeline: chunking документов -> эмбеддинги (с кэшем в Redis) ->
косинусная близость -> отсечение по порогу релевантности.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from hashlib import sha256
from math import sqrt

from src.application.interfaces.clients import EmbeddingClient, KeyValueStore
from src.application.interfaces.repositories import AbstractUserDocumentRepository
from src.config.settings import Settings
from src.utils.logging import log_event

logger = logging.getLogger(__name__)

_EMBEDDING_CACHE_PREFIX = "rag:emb:v1"


@dataclass(slots=True)
class DocumentChunk:
    """Фрагмент документа, подготовленный к векторному поиску."""

    document_id: int | None
    text: str


class RAGService:
    """Поиск релевантных фрагментов пользовательских документов.

    Сервис не выбрасывает исключения наружу: при недоступности сервиса
    эмбеддингов или отсутствии релевантных результатов возвращается
    пустой список, а ошибка фиксируется в логах.
    """

    def __init__(
        self,
        doc_repo: AbstractUserDocumentRepository,
        embed_client: EmbeddingClient,
        cache: KeyValueStore | None = None,
    ):
        """Инициализировать RAG-сервис.

        Args:
            doc_repo: Репозиторий пользовательских документов.
            embed_client: Клиент текстовых эмбеддингов.
            cache: Опциональное key-value хранилище для кэша эмбеддингов.
        """
        self._doc_repo = doc_repo
        self._embed_client = embed_client
        self._cache = cache

    async def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int | None = None,
    ) -> list[str]:
        """Найти релевантные фрагменты документов пользователя.

        Args:
            user_id: Идентификатор пользователя.
            query_text: Поисковый запрос.
            top_k: Максимальное число результатов (по умолчанию из настроек).

        Returns:
            Список релевантных фрагментов; пустой, если документов нет,
            запрос некорректен или сервис эмбеддингов недоступен.
        """
        query = str(query_text or "").strip()
        if not query:
            return []

        try:
            docs = await self._doc_repo.get_by_user(user_id)
        except Exception:
            log_event(
                logger,
                logging.ERROR,
                "rag.docs_load_failed",
                "Failed to load user docs",
                user_id=user_id,
            )
            return []
        if not docs:
            return []

        chunks = self._build_chunks(docs)
        if not chunks:
            return []

        try:
            query_embedding = (await self._embeddings([query]))[0]
            chunk_embeddings = await self._embeddings([chunk.text for chunk in chunks])
        except Exception as error:
            log_event(
                logger,
                logging.WARNING,
                "rag.embedding_failed",
                "Embedding service unavailable, RAG context skipped",
                user_id=user_id,
                error_type=type(error).__name__,
            )
            return []

        limit = top_k or Settings.rag_top_k
        scored = sorted(
            (
                (self._cosine_similarity(query_embedding, chunk_embedding), chunk)
                for chunk, chunk_embedding in zip(chunks, chunk_embeddings, strict=True)
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )
        results = [chunk.text for score, chunk in scored[:limit] if score >= Settings.rag_min_score]
        log_event(
            logger,
            logging.DEBUG,
            "rag.query_completed",
            "RAG query completed",
            user_id=user_id,
            chunks=len(chunks),
            results=len(results),
        )
        return results

    def _build_chunks(self, docs) -> list[DocumentChunk]:
        """Разбить документы на перекрывающиеся фрагменты заданного размера."""
        size = Settings.rag_chunk_size
        overlap = max(min(Settings.rag_chunk_overlap, size - 1), 0)
        step = size - overlap
        chunks: list[DocumentChunk] = []
        for doc in docs:
            text = " ".join(str(doc.content or "").split())
            for start in range(0, len(text), step):
                chunk = text[start : start + size]
                if len(chunk) < overlap + 1 and chunks and chunks[-1].document_id == doc.id:
                    continue
                chunks.append(DocumentChunk(document_id=doc.id, text=chunk))
        return chunks

    async def _embeddings(self, texts: list[str]) -> list[list[float]]:
        """Получить эмбеддинги с учётом кэша key-value хранилища."""
        if self._cache is None:
            return await self._embed_client.embed(texts)

        keys = [f"{_EMBEDDING_CACHE_PREFIX}:{self._text_hash(text)}" for text in texts]
        cached = [await self._cache.get_json(key) for key in keys]
        missing = [index for index, value in enumerate(cached) if not isinstance(value, list)]
        if missing:
            fresh = await self._embed_client.embed([texts[index] for index in missing])
            for index, vector in zip(missing, fresh, strict=True):
                cached[index] = vector
                await self._cache.set_json(
                    keys[index],
                    vector,
                    expire_seconds=Settings.rag_embedding_cache_ttl_seconds,
                )
        return [list(value) for value in cached]  # type: ignore[arg-type]

    @staticmethod
    def _text_hash(text: str) -> str:
        model = Settings.embedding_model
        return sha256(f"{model}:{text}".encode()).hexdigest()

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Вычислить косинусную близость двух векторов."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(ai * bi for ai, bi in zip(a, b, strict=True))
        norm_a = sqrt(sum(ai * ai for ai in a))
        norm_b = sqrt(sum(bi * bi for bi in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
