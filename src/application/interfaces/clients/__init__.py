"""Порты внешних клиентов и инфраструктурных сервисов.

Слой приложения зависит только от этих протоколов. Конкретные реализации
находятся в :mod:`src.infrastructures` и подключаются через DI-контейнер.
"""

from .blocklist import TokenBlocklist
from .database import DatabaseClient
from .embedding import EmbeddingClient
from .jwt import JWTService
from .llm import LLMClient
from .mailer import Mailer
from .password import PasswordService
from .pdf import PdfBuilder
from .rate_limiting import RateLimiter
from .storage import KeyValueStore
from .verification import EmailVerificationStore

__all__ = [
    "DatabaseClient",
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
