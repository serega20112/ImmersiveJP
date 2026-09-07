"""Порт клиента текстовых эмбеддингов."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingClient(Protocol):
    """Порт клиента текстовых эмбеддингов."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Вернуть векторы эмбеддингов для переданных текстов."""
        pass
