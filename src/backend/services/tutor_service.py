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
    role: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    audio_url: str | None = None


@dataclass
class TutorSession:
    id: int
    user_id: int
    document_id: int | None = None
    messages: list[TutorMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)


class TutorService:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        qwen_client: QwenClient,
        tts_client: TTSClient,
        document_analysis_service: DocumentAnalysisService,
    ) -> None:
        """Initialize the tutor service.

        Args:
            user_repository: Repository for user data access.
            qwen_client: Client for the Qwen LLM.
            tts_client: Client for text-to-speech synthesis.
            document_analysis_service: Service for document analysis.
        """
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
        """Start a new tutor session for the user.

        Args:
            user_id: ID of the user.
            document_id: Optional document ID to associate with the session.

        Returns:
            The newly created TutorSession instance.
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
            session_id: ID of the tutor session.
            message: The user's message text.

        Returns:
            The assistant's TutorMessage response.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        user = await self._user_repository.get_by_id(session.user_id)
        if not user:
            raise ValueError(f"User {session.user_id} not found")

        user_msg = TutorMessage(role="user", content=message)
        session.messages.append(user_msg)

        response = await self._generate_response(user, session, message)

        assistant_msg = TutorMessage(
            role="assistant",
            content=response["text"],
        )
        session.messages.append(assistant_msg)

        return assistant_msg

    async def _generate_response(
        self,
        _user: User,
        _session: TutorSession,
        message: str,
    ) -> dict[str, Any]:
        result = await self._qwen_client.analyze_document(message)
        return {
            "text": result.get("summary", "Я тебя понял. Чем можем помочь?"),
        }

    async def synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech audio from text.

        Args:
            text: The text to synthesize.

        Returns:
            The audio data as bytes.
        """
        return await self._tts_client.synthesize(text, lang="ru")
