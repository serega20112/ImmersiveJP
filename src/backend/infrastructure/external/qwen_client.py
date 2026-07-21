from __future__ import annotations

import json
import os
from typing import Any

import httpx

from src.backend.domain.content import TrackType
from src.backend.infrastructure.observability import get_logger

logger = get_logger(__name__)


class QwenClient:
    """LLM client for document analysis using Qwen models via OpenRouter.

    Used for analyzing user documents and extracting learning insights.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = os.getenv(
            "QWEN_MODEL",
            "qwen/qwen3-next-80b-a3b-instruct:free",
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "ImmersJP",
        }

    async def analyze_document(
        self,
        content: str,
        track: TrackType | None = None,
    ) -> dict[str, Any]:
        """Analyze a document and extract learning insights.

        Args:
            content: Document text content
            track: Optional learning track context

        Returns:
            Dictionary with analysis results:
            - topics: list of main topics
            - key_terms: list of key terms
            - difficulty: estimated difficulty level
            - summary: brief summary
        """
        system_prompt = (
            "Ты - ассистент по анализу учебных материалов. "
            "Проанализируй предоставленный текст и выдели основные темы, "
            "ключевые термины, оцени сложность и дай краткое содержание. "
            "Ответь строго в формате JSON без дополнительного текста."
        )

        user_prompt = f"""
Анализируй следующий учебный материал:

Текст:
{content[:8000]}

Формат ответа (JSON):
{{
    "topics": ["тема 1", "тема 2"],
    "key_terms": ["термин 1", "термин 2"],
    "difficulty": "beginner|basic|intermediate|advanced",
    "summary": "Краткое содержание не более 200 слов"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]

            try:
                return json.loads(raw_content)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse Qwen response as JSON",
                    extra={"raw": raw_content[:200]},
                )
                return {
                    "topics": [],
                    "key_terms": [],
                    "difficulty": "unknown",
                    "summary": raw_content[:200],
                }

    async def generate_questions(
        self,
        content: str,
        count: int = 3,
    ) -> list[str]:
        """Generate comprehension questions for the content.

        Args:
            content: Document text content
            count: Number of questions to generate

        Returns:
            List of question strings
        """
        system_prompt = (
            "Ты - помощник по созданию вопросов по учебным материалам. "
            "Создай вопросы для проверки понимания текста. "
            'Ответь строго в формате JSON: {"questions": ["вопрос 1", "вопрос 2"]}'
        )

        user_prompt = f"Создай {count} вопросов по следующему тексту:\n\n{content[:4000]}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 512,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]

            try:
                parsed = json.loads(raw_content)
                return parsed.get("questions", [])[:count]
            except json.JSONDecodeError:
                return [raw_content[:100]]
