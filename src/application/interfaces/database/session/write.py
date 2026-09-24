"""Порт записи репозитория учебных сессий."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import LearningSession


class LearningSessionWriteRepositoryPort(ABC):
    """Порт записи учебных сессий."""

    @abstractmethod
    async def save_track_session(self, session: LearningSession) -> LearningSession:
        """Создать или обновить сессию пользователя по треку.

        Принимает сущность целиком, а не отдельными полями: переходы между
        состояниями генерации принадлежат домену, и репозиторий обязан сохранить
        их все одним вызовом, чтобы номер партии и её статус не разъехались.

        Args:
            session: Сущность учебной сессии.

        Returns:
            Сохранённая сессия.
        """
        raise NotImplementedError
