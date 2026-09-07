"""Клиент эмбеддингов OpenRouter."""

from __future__ import annotations

import httpx

from src.config.settings import settings


class EmbeddingClient:
    """Клиент векторных представлений текста через OpenRouter embeddings API."""

    def __init__(self) -> None:
        self._api_key = settings.llm.openrouter_api_key
        self._base_url = "https://openrouter.ai/api/v1/embeddings"
        self._model = settings.llm.embedding_model
        self._timeout = httpx.Timeout(15.0)

    @property
    def configured(self) -> bool:
        """Возвращает True, если задан API-ключ OpenRouter."""
        return bool(self._api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Вернуть векторы эмбеддингов для переданных текстов.

        Args:
            texts: Непустой список текстов.

        Returns:
            Список векторов той же длины, что и входные тексты.

        Raises:
            EmbeddingError: Если ключ не настроен или API вернул ошибку.
        """
        if not texts:
            return []
        if not self._api_key:
            raise EmbeddingError("OPENROUTER_API_KEY is not configured")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._base_url,
                    json={"model": self._model, "input": texts},
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as error:
            raise EmbeddingError(f"Embedding request failed: {error}") from error
        try:
            return [item["embedding"] for item in data["data"]]
        except (KeyError, TypeError) as error:
            raise EmbeddingError(f"Unexpected embeddings response shape: {data!r}") from error


class EmbeddingError(RuntimeError):
    """Ошибка обращения к сервису эмбеддингов."""
