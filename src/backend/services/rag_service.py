from __future__ import annotations

from math import sqrt
from typing import Sequence

from src.backend.infrastructure.external import EmbeddingClient
from src.backend.infrastructure.repositories import AbstractUserDocumentRepository


class RAGService:
    def __init__(
        self,
        doc_repo: AbstractUserDocumentRepository,
        embed_client: EmbeddingClient,
    ):
        self._doc_repo = doc_repo
        self._embed_client = embed_client

    async def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 3,
    ) -> Sequence[str]:
        docs = await self._doc_repo.get_by_user(user_id)
        if not docs:
            return []

        query_emb = (await self._embed_client.embed([query_text]))[0]
        doc_texts = [doc.content for doc in docs]

        doc_embs = await self._embed_client.embed(doc_texts)

        scored = [
            (self._cosine_similarity(query_emb, doc_emb), doc_texts[i])
            for i, doc_emb in enumerate(doc_embs)
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        threshold = 0.4
        return [
            text[:1200]
            for score, text in scored[:top_k]
            if score > threshold
        ]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(ai * bi for ai, bi in zip(a, b))
        norm_a = sqrt(sum(ai * ai for ai in a))
        norm_b = sqrt(sum(bi * bi for bi in b))
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot / (norm_a * norm_b)
