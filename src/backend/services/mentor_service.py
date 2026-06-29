from src.backend.services.document_service import DocumentService
from src.backend.services.rag_service import RAGService
from src.backend.infrastructure.external.llm_client import LLMClient
from src.backend.infrastructure.external.tts_client import TTSClient
from src.backend.infrastructure.repositories.user_document_repository import UserDocumentRepository
from sqlalchemy.orm import Session

class MentorService:
    """Service that provides AI‑tutor functionality.

    Combines document retrieval (RAG), language model generation and
    text‑to‑speech synthesis.

    Args:
        doc_repo: Repository for user documents.
        rag_service: Service for retrieving relevant document chunks.
        llm_client: Client for chatting with the language model.
        tts_client: Client for synthesising speech.
    """
    def __init__(
        self,
        doc_repo: UserDocumentRepository,
        rag_service: RAGService,
        llm_client: LLMClient,
        tts_client: TTSClient,
    ):
        self.doc_repo = doc_repo
        self.rag_service = rag_service
        self.llm_client = llm_client
        self.tts_client = tts_client

    async def answer(
        self,
        user_id: int,
        question: str,
    ) -> tuple[str, bytes]:
        """Generate an answer to ``question`` for ``user_id`` and return
        both the text and its spoken form.

        Returns:
            Tuple of (answer_text, audio_bytes).
        """
        # Retrieve relevant documents
        relevant_docs = await self.rag_service.query(user_id, question)
        context = "\n\n".join([doc.content for doc in relevant_docs if doc])

        # Build prompt for LLM
        system_prompt = (
            "You are a helpful tutor. Use the provided context from the "
            "user's study materials to answer the question. If the context "
            "does not contain enough information, say you don't know."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        answer_text = await self.llm_client.chat(messages)

        # Synthesize speech
        audio_bytes = await self.tts_client.synthesize(answer_text)

        return answer_text, audio_bytes