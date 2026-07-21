from __future__ import annotations

from datetime import datetime

from src.backend.dependencies.settings import Settings
from src.backend.domain.mentor import MentorFocus, MentorMessage
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.repositories import (
    AbstractMentorRepository,
    AbstractUserRepository,
)
from src.backend.services.rag_service import RAGService
from src.backend.use_case.profile.build_learning_plan import BuildLearningPlanUseCase
from src.backend.use_case.profile.build_progress_report import (
    BuildProgressReportUseCase,
)
from src.backend.use_case.profile.get_mentor_page import GetMentorPageUseCase


class InvalidMentorMessageError(Exception):
    pass


class SendMentorMessageUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        mentor_repository: AbstractMentorRepository,
        build_progress_report_use_case: BuildProgressReportUseCase,
        build_learning_plan_use_case: BuildLearningPlanUseCase,
        get_mentor_page_use_case: GetMentorPageUseCase,
        llm_client: HuggingFaceLLMClient,
        rag_service: RAGService | None = None,
    ):
        """Initialize the send mentor message use case.

        Args:
            user_repository: Repository for user data.
            mentor_repository: Repository for mentor data.
            build_progress_report_use_case: Use case for building progress reports.
            build_learning_plan_use_case: Use case for building learning plans.
            get_mentor_page_use_case: Use case for getting the mentor page.
            llm_client: Client for LLM chat completions.
            rag_service: Optional RAG service for document context.
        """
        self._user_repository = user_repository
        self._mentor_repository = mentor_repository
        self._build_progress_report_use_case = build_progress_report_use_case
        self._build_learning_plan_use_case = build_learning_plan_use_case
        self._get_mentor_page_use_case = get_mentor_page_use_case
        self._llm_client = llm_client
        self._rag_service = rag_service

    async def execute(self, user_id: int, message_text: str):
        """Send a mentor message and return the updated mentor page.

        Args:
            user_id: ID of the user.
            message_text: The message text to send.

        Returns:
            The updated mentor page data.

        Raises:
            InvalidMentorMessageError: If the message is invalid.
        """
        message = str(message_text or "").strip()
        if not message:
            raise InvalidMentorMessageError("Сообщение пустое. Сформулируй, что именно не идет.")
        if len(message) > Settings.text_input_limit:
            raise InvalidMentorMessageError(
                f"Сообщение ограничено {Settings.text_input_limit} символами"
            )

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        history = await self._mentor_repository.get_messages(user_id)
        active_focus = await self._mentor_repository.get_focus(user_id)
        detected_focus = self._detect_focus(message)
        if detected_focus is not None:
            active_focus = detected_focus
            await self._mentor_repository.set_focus(user_id, active_focus)

        report = await self._build_progress_report_use_case.execute(user_id)
        plan = await self._build_learning_plan_use_case.execute(user_id)

        document_context = ""
        if self._rag_service is not None:
            context_chunks = await self._rag_service.query(user_id, message)
            if context_chunks:
                document_context = "\n---\n".join(context_chunks)

        reply = await self._llm_client.generate_mentor_reply(
            user=user,
            report=report,
            plan=plan,
            message=message,
            history=history[-6:],
            active_focus=active_focus,
            document_context=document_context,
        )

        updated_history = [
            *history,
            MentorMessage(
                role="user",
                content=message,
                created_at=datetime.utcnow(),
            ),
            MentorMessage(
                role="assistant",
                content=reply.reply,
                created_at=datetime.utcnow(),
                action_steps=list(reply.action_steps),
            ),
        ][-12:]
        await self._mentor_repository.save_messages(user_id, updated_history)
        return await self._get_mentor_page_use_case.execute(user_id)

    @staticmethod
    def _detect_focus(message: str) -> MentorFocus | None:
        """Detect the mentor focus from a message.

        Args:
            message: The message text to analyze.

        Returns:
            The detected mentor focus, or None.
        """
        mapping = (
            (
                ("кандзи", "kanji", "кандз"),
                MentorFocus(
                    key="kanji",
                    title="Упор на кандзи",
                    note="В следующих языковых партиях усили чтение кандзи, базовые знаки, чтение в словах и короткие упражнения на узнавание.",
                ),
            ),
            (
                ("частиц", "particle", "grammar", "граммат", "граммати"),
                MentorFocus(
                    key="grammar",
                    title="Упор на грамматику",
                    note="В следующих языковых партиях усили частицы, базовый порядок предложения, отрицание и короткие сцены на грамматический выбор.",
                ),
            ),
            (
                ("разговор", "речь", "speaking", "говор", "speech"),
                MentorFocus(
                    key="speech",
                    title="Упор на речь",
                    note="В следующих языковых партиях усили короткие диалоги, бытовые реакции, просьбы и связки для устной практики.",
                ),
            ),
        )
        normalized_message = message.casefold()
        for keywords, focus in mapping:
            if any(keyword in normalized_message for keyword in keywords):
                return focus
        return None
