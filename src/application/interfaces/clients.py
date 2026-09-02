"""Порты (интерфейсы) внешних клиентов и инфраструктурных сервисов.

Слой приложения зависит только от этих протоколов. Конкретные реализации
находятся в :mod:`src.infrastructures` и подключаются через DI-контейнер.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from src.application.dto.learning import (
    GeneratedCardDraftDTO,
    SpeechPracticeDTO,
    TrackWorkResultDTO,
)
from src.application.dto.learning_dto import TrackCardDTO
from src.application.dto.mentor_dto import MentorReplyDTO
from src.application.dto.profile_dto import (
    AIAdviceDTO,
    LearningPlanPageDTO,
    ProgressReportDTO,
)
from src.domain.content import TrackType
from src.domain.user import User


@runtime_checkable
class LLMClient(Protocol):
    """Порт LLM-клиента для генерации учебного контента."""

    async def generate_cards(
        self,
        user: User,
        track: TrackType,
        batch_number: int,
        batch_size: int,
        previous_topics: list[str],
    ) -> list[GeneratedCardDraftDTO]:
        """Сгенерировать черновики карточек для нового батча."""
        ...

    async def generate_advice(self, user: User, report: ProgressReportDTO) -> AIAdviceDTO:
        """Сгенерировать персональный совет по прогрессу."""
        ...

    async def generate_speech_practice(
        self,
        user: User,
        words: list[str],
    ) -> SpeechPracticeDTO:
        """Сгенерировать упражнение на отработку слов."""
        ...

    async def generate_mentor_reply(
        self,
        *,
        user: User,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
    ) -> MentorReplyDTO:
        """Сгенерировать ответ ментора на сообщение пользователя."""
        ...

    async def generate_knowledge_check(
        self,
        *,
        user: User,
        weak_points: list[str] | None = None,
        strengths: list[str] | None = None,
        recent_topics: list[str] | None = None,
        focus_area: str = "",
    ) -> list[dict[str, Any]]:
        """Сгенерировать вопросы для проверки знаний."""
        ...

    async def evaluate_knowledge_check(
        self,
        *,
        user_id: int = 0,
        questions: list[dict[str, Any]],
        answers: dict[str, str],
    ) -> dict[str, Any]:
        """Оценить ответы пользователя на вопросы проверки."""
        ...

    async def review_track_work(
        self,
        *,
        user: User,
        track: TrackType,
        batch_number: int,
        tasks: list[dict[str, object]],
        answers: dict[str, str],
    ) -> TrackWorkResultDTO:
        """Проверить домашнюю работу по треку."""
        ...

    async def close(self) -> None:
        """Освободить ресурсы клиента."""
        ...


@runtime_checkable
class EmbeddingClient(Protocol):
    """Порт клиента текстовых эмбеддингов."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Вернуть векторы эмбеддингов для переданных текстов."""
        ...


@runtime_checkable
class PdfBuilder(Protocol):
    """Порт сборщика PDF-документов."""

    async def build_cards_pdf(
        self,
        user_display_name: str,
        track: TrackType,
        cards: list[TrackCardDTO],
    ) -> bytes:
        """Собрать PDF с карточками и вернуть содержимое файла."""
        ...


@runtime_checkable
class Mailer(Protocol):
    """Порт отправки электронной почты."""

    async def send_verification_code(self, email: str, code: str) -> None:
        """Отправить письмо с кодом подтверждения."""
        ...


@runtime_checkable
class PasswordService(Protocol):
    """Порт хеширования и проверки паролей."""

    def hash_password(self, password: str) -> str:
        """Вернуть хеш пароля."""
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Проверить пароль против хеша."""
        ...


@runtime_checkable
class JWTService(Protocol):
    """Порт выпуска и разбора JWT-токенов."""

    def create_access_token(self, user_id: int) -> str:
        """Выпустить access-токен."""
        ...

    def create_refresh_token(self, user_id: int) -> str:
        """Выпустить refresh-токен."""
        ...

    def decode_access_token(self, token: str) -> int:
        """Разобрать access-токен и вернуть идентификатор пользователя."""
        ...

    def decode_refresh_token(self, token: str) -> int:
        """Разобрать refresh-токен и вернуть идентификатор пользователя."""
        ...

    def get_token_ttl_seconds(self, token: str) -> int:
        """Вернуть остаток времени жизни токена в секундах."""
        ...


@runtime_checkable
class TokenBlocklist(Protocol):
    """Порт хранилища отозванных токенов."""

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Отозвать токен на время оставшейся жизни."""
        ...

    async def is_revoked(self, token: str) -> bool:
        """Проверить, отозван ли токен."""
        ...


@runtime_checkable
class EmailVerificationStore(Protocol):
    """Порт хранилища кодов подтверждения email."""

    async def issue_code(self, email: str) -> str:
        """Выдать и сохранить новый код подтверждения."""
        ...

    async def verify_code(self, email: str, code: str) -> bool:
        """Проверить код подтверждения."""
        ...


@runtime_checkable
class RateLimiter(Protocol):
    """Порт ограничителя частоты запросов."""

    async def consume(self, scope: str, key: str, window_seconds: int) -> int:
        """Увеличить счётчик в окне и вернуть текущее значение."""
        ...

    async def is_allowed(self, scope: str, key: str, limit: int, window_seconds: int) -> bool:
        """Проверить, не превышен ли лимит запросов."""
        ...


@runtime_checkable
class KeyValueStore(Protocol):
    """Порт key-value хранилища (Redis или in-memory)."""

    async def get_json(self, key: str) -> Any:
        """Получить JSON-значение по ключу."""
        ...

    async def set_json(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        """Сохранить JSON-значение с опциональным TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Удалить ключ."""
        ...

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Инкрементировать счётчик и задать TTL."""
        ...

    async def close(self) -> None:
        """Закрыть соединение с хранилищем."""
        ...
