"""Fix dependency-rule violations in the application layer and remove dead code."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEAD_FILES = [
    "src/application/services/document_service.py",
    "src/application/services/document_analysis_service.py",
    "src/application/services/tutor_service.py",
    "src/application/services/mentor_service.py",
    "src/application/interfaces/repositories/user_document_repository.py",
]

# Whole-repo import rewrites (safe: these modules keep the same public API).
GLOBAL_RULES = [
    (
        "from src.config.settings import",
        "from src.config.settings import",
    ),
    (
        "from src.utils.logging import get_logger, log_event",
        "from src.utils.logging import get_logger, log_event",
    ),
]

# Rules applied only inside src/application (dependency rule enforcement).
APP_RULES = [
    (
        "from src.infrastructures.external import HuggingFaceLLMClient",
        "from src.application.interfaces.clients import LLMClient",
    ),
    ("HuggingFaceLLMClient", "LLMClient"),
    (
        "from src.infrastructures.external import EmbeddingClient",
        "from src.application.interfaces.clients import EmbeddingClient",
    ),
    (
        "from src.infrastructures.external import PdfBuilder",
        "from src.application.interfaces.clients import PdfBuilder",
    ),
    (
        "from src.infrastructures.external import Mailer",
        "from src.application.interfaces.clients import Mailer",
    ),
    (
        "from src.infrastructures.security import EmailVerificationStore",
        "from src.application.interfaces.clients import EmailVerificationStore",
    ),
    (
        "from src.infrastructures.security import JWTService, TokenBlocklist",
        "from src.application.interfaces.clients import JWTService, TokenBlocklist",
    ),
    (
        "from src.infrastructures.security import EmailVerificationStore, PasswordService",
        "from src.application.interfaces.clients import EmailVerificationStore, PasswordService",
    ),
    (
        "from src.infrastructures.security import JWTService, PasswordService",
        "from src.application.interfaces.clients import JWTService, PasswordService",
    ),
    (
        "from src.infrastructures.security import RateLimiter",
        "from src.application.interfaces.clients import RateLimiter",
    ),
    (
        "from src.infrastructures.cache import KeyValueStore",
        "from src.application.interfaces.clients import KeyValueStore",
    ),
]

UTILS_LOGGING = '''"""Нейтральные помощники логирования, доступные всем слоям."""

from __future__ import annotations

import logging
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Вернуть именованный logger.

    Args:
        name: Имя логгера, обычно ``__name__`` модуля.

    Returns:
        Настроенный стандартный logger.
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    """Записать структурированное событие в лог.

    Args:
        logger: Целевой логгер.
        level: Уровень записи (например, ``logging.INFO``).
        event: Машиночитаемый код события.
        message: Человекочитаемое описание.
        **fields: Дополнительные структурированные поля события.
    """
    logger.log(level, message, extra={"event": event, "extra_fields": fields})
'''

UTILS_INIT = '''"""Общие утилиты, не зависящие от слоёв приложения."""

from .logging import get_logger, log_event

__all__ = ["get_logger", "log_event"]
'''

DOMAIN_DOCUMENTS = '''"""Доменная сущность пользовательского документа."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserDocument:
    """Пользовательский конспект: заголовок и текстовое содержимое."""

    id: int | None
    user_id: int
    title: str
    content: str
    created_at: datetime | None = None
'''

NEW_ABSTRACT = '''"""Интерфейс репозитория пользовательских документов."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.documents import UserDocument


class AbstractUserDocumentRepository(ABC):
    """Контракт доступа к пользовательским документам."""

    @abstractmethod
    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Создать документ пользователя."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Вернуть все документы пользователя."""

    @abstractmethod
    async def get(self, doc_id: int) -> UserDocument | None:
        """Вернуть документ по идентификатору или ``None``."""

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору."""
'''

NEW_IMPL = '''"""SQLAlchemy-реализация репозитория пользовательских документов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.abstract_user_document_repository import (
    AbstractUserDocumentRepository,
)
from src.domain.documents import UserDocument
from src.infrastructures.database.models.user_document_model import (
    UserDocument as UserDocumentModel,
)


class UserDocumentRepository(AbstractUserDocumentRepository):
    """Репозиторий документов поверх PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Инициализировать репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def create(self, user_id: int, title: str, content: str) -> UserDocument:
        """Создать новый документ пользователя.

        Args:
            user_id: Идентификатор пользователя.
            title: Заголовок документа.
            content: Текстовое содержимое документа.

        Returns:
            Созданная доменная сущность документа.
        """
        doc = UserDocumentModel(user_id=user_id, title=title, content=content)
        self._session.add(doc)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(doc)
        return self._to_entity(doc)

    async def get_by_user(self, user_id: int) -> list[UserDocument]:
        """Получить все документы пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Список доменных сущностей документов.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.user_id == user_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get(self, doc_id: int) -> UserDocument | None:
        """Получить документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.

        Returns:
            Доменная сущность документа или ``None``.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def delete(self, doc_id: int) -> None:
        """Удалить документ по идентификатору.

        Args:
            doc_id: Идентификатор документа.
        """
        result = await self._session.execute(
            select(UserDocumentModel).where(UserDocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: UserDocumentModel) -> UserDocument:
        """Преобразовать ORM-модель в доменную сущность."""
        return UserDocument(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
        )
'''

INTERFACES_INIT = '''"""Порты слоя приложения: репозитории и внешние клиенты."""

from .clients import (
    EmailVerificationStore,
    EmbeddingClient,
    JWTService,
    KeyValueStore,
    LLMClient,
    Mailer,
    PasswordService,
    PdfBuilder,
    RateLimiter,
    TokenBlocklist,
)

__all__ = [
    "EmailVerificationStore",
    "EmbeddingClient",
    "JWTService",
    "KeyValueStore",
    "LLMClient",
    "Mailer",
    "PasswordService",
    "PdfBuilder",
    "RateLimiter",
    "TokenBlocklist",
]
'''


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    for rel in DEAD_FILES:
        p = ROOT / rel
        if p.exists():
            try:
                git("rm", "-q", rel)
            except subprocess.CalledProcessError:
                p.unlink()
            print(f"deleted: {rel}")

    (ROOT / "src/utils").mkdir(exist_ok=True)
    (ROOT / "src/utils/__init__.py").write_text(UTILS_INIT, encoding="utf-8", newline="\n")
    (ROOT / "src/utils/logging.py").write_text(UTILS_LOGGING, encoding="utf-8", newline="\n")
    (ROOT / "src/domain/documents.py").write_text(DOMAIN_DOCUMENTS, encoding="utf-8", newline="\n")
    (ROOT / "src/domain/__init__.py").write_text(
        (ROOT / "src/domain/__init__.py").read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    (ROOT / "src/application/interfaces/repositories/abstract_user_document_repository.py").write_text(
        NEW_ABSTRACT, encoding="utf-8", newline="\n"
    )
    (ROOT / "src/infrastructures/repositories/implementations/user_document_repository.py").write_text(
        NEW_IMPL, encoding="utf-8", newline="\n"
    )
    (ROOT / "src/application/interfaces/__init__.py").write_text(
        INTERFACES_INIT, encoding="utf-8", newline="\n"
    )
    print("wrote new files")

    for py in ROOT.rglob("*.py"):
        parts = py.parts
        if ".venv" in parts or "__pycache__" in parts or ".git" in parts:
            continue
        text = py.read_text(encoding="utf-8")
        new_text = text
        for old, new in GLOBAL_RULES:
            new_text = new_text.replace(old, new)
        rel = py.relative_to(ROOT).as_posix()
        if rel.startswith("src/application"):
            for old, new in APP_RULES:
                new_text = new_text.replace(old, new)
        if new_text != text:
            py.write_text(new_text, encoding="utf-8", newline="\n")
            print(f"rewritten: {rel}")

    return 0


if __name__ == "__main__":
    sys.exit(main())