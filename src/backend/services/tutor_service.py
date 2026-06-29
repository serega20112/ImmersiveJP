from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.backend.domain.user import User
from src.backend.infrastructure.external.qwen_client import QwenClient
from src.backend.infrastructure.external.tts_client import TTSClient
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.services.document_analysis_service import DocumentAnalysisService


@dataclass
class TutorMessage:
    """A message in the tutor conversation."""

    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    audio_url: str | None = None


@dataclass
class TutorSession:
    """A tutoring session with the AI tutor."""

    id: int
    user_id: int
    document_id: int | None = None
    messages: list[TutorMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)


class TutorService:
    """Service that provides AI tutoring functionality.

    Combines document analysis, conversation, and voice synthesis.
    """

    def __init__(
        self,
        user_repository: AbstractUserRepository,
        qwen_client: QwenClient,
        tts_client: TTSClient,
        document_analysis_service: DocumentAnalysisService,
    ):
        self._user_repository = user_repository
        self._qwen_client = qwen_client
        self._tts_client = tts_client
        self._doc_analysis = document_analysis_service
        self._sessions: dict[int, TutorSession] = {}

    async def start_session(
        self,
        user_id: int,
        document_id: int | None = None,
    ) -> TutorSession:
        """Start a new tutoring session.

        Args:
            user_id: ID of the user
            document_id: Optional document ID to focus on

        Returns:
            New TutorSession
        """
        session_id = len(self._sessions) + 1
        session = TutorSession(
            id=session_id,
            user_id=user_id,
            document_id=document_id,
        )
        self._sessions[session_id] = session
        return session

    async def send_message(
        self,
        session_id: int,
        message: str,
    ) -> TutorMessage:
        """Send a message to the tutor and get a response.

        Args:
            session_id: Session ID
            message: User message

        Returns:
            TutorMessage with response and optional audio
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        user = await self._user_repository.get_by_id(session.user_id)
        if not user:
            raise ValueError(f"User {session.user_id} not found")

        # Add user message
        user_msg = TutorMessage(role="user", content=message)
        session.messages.append(user_msg)

        # Generate response
        response = await self._generate_response(user, session, message)

        # Add assistant message
        assistant_msg = TutorMessage(
            role="assistant",
            content=response["text"],
        )
        session.messages.append(assistant_msg)

        return assistant_msg

    async def _generate_response(
        self,
        user: User,
        session: TutorSession,
        message: str,
    ) -> dict[str, Any]:
        """Generate tutor response using Qwen."""
        # Build context from session history
        history = "\n".join(
            f"{m.role}: {m.content}" for m in session.messages[-6:]
        )

        # Build prompt
        system_prompt = (
            "Ты - репетитор ImmersJP. Отвечай на русском языке. "
            "Объясняй материал понятно, задавай уточняющие вопросы. "
            "Адаптируй ответ под уровень пользователя."
        )

        user_prompt = f"""
Пользователь спросил: {message}

История диалога:
{history}

Ответь кратко и по делу. Если нужно, задай вопрос для уточнения.
"""

        result = await self._qwen_client.analyze_document(message)
        return {
            "text": result.get("summary", "Я тебя понял. Чем можем помочь?"),
        }

    async def synthesize_speech(self, text: str) -> bytes:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize

        Returns:
            MP3 audio bytes
        """
        return await self._tts_client.synthesize(text, lang="ru")