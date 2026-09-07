"""Доменные сервисы с чистой логикой без внешних зависимостей."""

from .text_search import chunk_documents, cosine_similarity

__all__ = [
    "chunk_documents",
    "cosine_similarity",
]
