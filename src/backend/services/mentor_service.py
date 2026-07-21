from __future__ import annotations

from src.backend.infrastructure.external.llm_client import LLMClient
from src.backend.infrastructure.external.tts_client import TTSClient
from src.backend.infrastructure.repositories.user_document_repository import (
    UserDocumentRepository,
)
from src.backend.services.rag_service import RAGService


class MentorService:
    def __init__(
        self,
        doc_repo: UserDocumentRepository,
        rag_service: RAGService,
        llm_client: LLMClient,
        tts_client: TTSClient,
    ) -> None:
        """Initialize the mentor service.

        Args:
            doc_repo: Repository for user documents.
            rag_service: RAG service for relevant context retrieval.
            llm_client: Client for LLM chat completions.
            tts_client: Client for text-to-speech synthesis.
        """
        self.doc_repo = doc_repo
        self.rag_service = rag_service
        self.llm_client = llm_client
        self.tts_client = tts_client

    async def answer(
        self,
        user_id: int,
        question: str,
    ) -> tuple[str, bytes]:
        """Answer a user's question using RAG and LLM.

        Args:
            user_id: ID of the user.
            question: The user's question text.

        Returns:
            A tuple of (answer_text, audio_bytes).
        """
        relevant_docs = await self.rag_service.query(user_id, question)
        context = "\n\n".join([doc for doc in relevant_docs if doc])

        system_prompt = (
            "You are a helpful tutor. Use the provided context from the "
            "user's study materials to answer the question. If the context "
            "does not contain enough information, say you don't know."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ]

        answer_text = await self.llm_client.chat(messages)
        audio_bytes = await self.tts_client.synthesize(answer_text)

        return answer_text, audio_bytes
