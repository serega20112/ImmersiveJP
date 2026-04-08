from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.domain.mentor import MentorFocus, MentorMessage


class AbstractMentorRepository(ABC):
    @abstractmethod
    async def get_messages(self, user_id: int) -> list[MentorMessage]:
        pass

    @abstractmethod
    async def save_messages(self, user_id: int, messages: list[MentorMessage]) -> None:
        pass

    @abstractmethod
    async def get_focus(self, user_id: int) -> MentorFocus | None:
        pass

    @abstractmethod
    async def set_focus(self, user_id: int, focus: MentorFocus | None) -> None:
        pass
