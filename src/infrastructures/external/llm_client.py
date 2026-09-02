from __future__ import annotations

import os

import httpx


class LLMClient:
    """Client for OpenRouter LLM inference.

    The model is taken from ``LLM_MODEL`` env var, defaults to
    ``openai/gpt-oss-120b:free`` which is available on OpenRouter.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Compass",
        }

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        """Send chat messages and receive the assistant's reply."""
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.base_url, json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
