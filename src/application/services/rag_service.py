"""Сервис RAG: поиск релевантных фрагментов в документах пользователя.

Pipeline: загрузка документов (UoW) -> chunking (домен) -> эмбеддинги
(инфраструктура, с кэшем) -> ранжирование по косинусной близости (домен).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from hashlib import sha256

from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import EmbeddingClient
from src.application.interfaces.exceptions import InfrastructureError
from src.config.settings import settings
from src.domain.entities import UserDocument
from src.domain.services import chunk_documents, cosine_similarity
from src.utils.logging import log_event

logger = logging.getLogger(__name__)

_EMBEDDING_CACHE_PREFIX = "rag:emb:v1"


class RAGService:
    """Поиск релевантных фрагментов пользовательских документов.

    Наружу не выпускаются только отказы инфраструктуры: недоступность базы или
    сервиса эмбеддингов — штатная ситуация, и контекст просто не добавляется в
    ответ. Собственный дефект (опечатка, неверная форма данных) обязан упасть:
    перехват его молча пустым списком превратил бы ошибку сборки в тихое
    «пользователь ничего не получает».
    """

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        embed_client: EmbeddingClient,
    ):
        """Инициализировать RAG-сервис.

        Args:
            uow_factory: Фабрика Unit of Work для получения документов.
            embed_client: Клиент эмбеддингов с кэшированием.
        """
        self._uow_factory = uow_factory
        self._embed_client = embed_client

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
            documents = await self._load_documents(user_id)
        except InfrastructureError as error:
            log_event(
                logger,
                logging.ERROR,
                "rag.docs_load_failed",
                "Failed to load user docs",
                user_id=user_id,
                error_type=type(error).__name__,
                error=str(error),
            )
            return []
        if not documents:
            return []

        chunks = chunk_documents(
            documents,
            chunk_size=settings.rag.rag_chunk_size,
            chunk_overlap=settings.rag.rag_chunk_overlap,
        )
        if not chunks:
            return []

        try:
            query_embedding = (await self._embeddings([query]))[0]
            chunk_embeddings = await self._embeddings([chunk.text for chunk in chunks])
        except InfrastructureError as error:
            log_event(
                logger,
                logging.WARNING,
                "rag.embedding_failed",
                "Embedding service unavailable, RAG context skipped",
                user_id=user_id,
                error_type=type(error).__name__,
                error=str(error),
            )
            return []

        limit = top_k or settings.rag.rag_top_k
        scored = sorted(
            (
                (cosine_similarity(query_embedding, chunk_embedding), chunk)
                for chunk, chunk_embedding in zip(chunks, chunk_embeddings, strict=True)
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )
        results = [
            chunk.text for score, chunk in scored[:limit] if score >= settings.rag.rag_min_score
        ]
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

    async def _load_documents(self, user_id: int) -> list[UserDocument]:
        """Загрузить документы пользователя через Unit of Work.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Список документов пользователя.
        """
        async with self._uow_factory() as uow:
            doc_repository = uow.user_documents
            return await doc_repository.get_by_user(user_id)

    async def _embeddings(self, texts: list[str]) -> list[list[float]]:
        """Получить эмбеддинги через клиент с кэшированием.

        Args:
            texts: Тексты для векторизации.

        Returns:
            Список векторов эмбеддингов.
        """
        return await self._embed_client.embed(texts)

    @staticmethod
    def embedding_cache_key(text: str) -> str:
        """Построить ключ кэша эмбеддинга для текста.

        Args:
            text: Исходный текст.

        Returns:
            Ключ кэша с учётом модели эмбеддингов.
        """
        model = settings.llm.embedding_model
        return f"{_EMBEDDING_CACHE_PREFIX}:{sha256(f'{model}:{text}'.encode()).hexdigest()}"
