from __future__ import annotations

from dataclasses import dataclass

from src.backend.domain.content import TrackType
from src.backend.infrastructure.external.qwen_client import QwenClient


@dataclass
class DocumentAnalysis:
    """Result of document analysis."""

    topics: list[str]
    key_terms: list[str]
    difficulty: str
    summary: str


class DocumentAnalysisService:
    """Service for analyzing user documents and extracting learning insights."""

    def __init__(self, qwen_client: QwenClient):
        self._qwen_client = qwen_client

    async def analyze(
        self,
        content: str,
        track: TrackType | None = None,
    ) -> DocumentAnalysis:
        """Analyze document content and return insights.

        Args:
            content: Document text content
            track: Optional learning track context

        Returns:
            DocumentAnalysis with topics, key_terms, difficulty, summary
        """
        result = await self._qwen_client.analyze_document(content, track)
        return DocumentAnalysis(
            topics=result.get("topics", []),
            key_terms=result.get("key_terms", []),
            difficulty=result.get("difficulty", "unknown"),
            summary=result.get("summary", ""),
        )

    async def generate_questions(
        self,
        content: str,
        count: int = 3,
    ) -> list[str]:
        """Generate comprehension questions for the document.

        Args:
            content: Document text content
            count: Number of questions to generate

        Returns:
            List of question strings
        """
        return await self._qwen_client.generate_questions(content, count)