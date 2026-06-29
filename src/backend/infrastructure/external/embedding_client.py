import os
import httpx
from typing import List

class EmbeddingClient:
    """Simple client for OpenRouter embedding endpoint.

    Uses the model specified in ``EMBEDDING_MODEL`` env var, defaults to
    ``text-embedding-ada-002`` which is free on OpenRouter.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/embeddings"
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "http://localhost", "X-Title": "Compass"}

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return list of embedding vectors for given texts."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.base_url, json={"model": self.model, "input": texts}, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
