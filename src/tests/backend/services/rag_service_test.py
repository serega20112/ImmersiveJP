"""Unit-тесты RAG-сервиса на фейках без БД и внешних API."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.services.rag_service import RAGService
from src.tests.support import FakeUnitOfWork


@dataclass(slots=True)
class FakeDoc:
    id: int
    content: str


class FakeDocRepo:
    def __init__(self, docs: list[FakeDoc]):
        self._docs = docs

    async def get_by_user(self, user_id: int) -> list[FakeDoc]:
        return self._docs


class FakeEmbedClient:
    def __init__(self, vectors_by_text: dict[str, list[float]]):
        self._vectors = vectors_by_text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors[text] for text in texts]


class FailingEmbedClient:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("unavailable")


def _rag_service(docs: list[FakeDoc], embed_client) -> RAGService:
    return RAGService(
        lambda: FakeUnitOfWork({"user_document": FakeDocRepo(docs)}),
        embed_client,
    )


@pytest.mark.asyncio
async def test_query_returns_relevant_chunk():
    target = "Токио столица Японии и крупнейший город страны"
    other = "Кандзи это китайские иероглифы используемые в письменности"
    vectors = {
        "токио": [1.0, 0.0, 0.0],
        target: [0.9, 0.1, 0.0],
        other: [0.0, 0.0, 1.0],
    }
    service = _rag_service(
        [FakeDoc(id=1, content=other), FakeDoc(id=2, content=target)],
        FakeEmbedClient(vectors),
    )
    results = await service.query(1, "токио", top_k=2)
    assert results == [target]


@pytest.mark.asyncio
async def test_query_empty_query_returns_empty():
    service = _rag_service([], FakeEmbedClient({}))
    assert await service.query(1, "   ") == []


@pytest.mark.asyncio
async def test_query_no_documents_returns_empty():
    service = _rag_service([], FakeEmbedClient({}))
    assert await service.query(1, "любой запрос") == []


@pytest.mark.asyncio
async def test_query_embedding_failure_degrades_gracefully():
    service = _rag_service(
        [FakeDoc(id=1, content="какой-то текст")],
        FailingEmbedClient(),
    )
    assert await service.query(1, "запрос") == []


@pytest.mark.asyncio
async def test_query_filters_by_min_score():
    service = _rag_service(
        [FakeDoc(id=1, content="нерелевантный фрагмент про кандзи")],
        FakeEmbedClient(
            {
                "запрос": [1.0, 0.0],
                "нерелевантный фрагмент про кандзи": [0.0, 1.0],
            }
        ),
    )
    assert await service.query(1, "запрос") == []
