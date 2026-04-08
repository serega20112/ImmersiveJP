from __future__ import annotations

from datetime import datetime

from src.backend.domain.mentor import MentorFocus, MentorMessage
from src.backend.infrastructure.cache import KeyValueStore
from src.backend.infrastructure.repositories import AbstractMentorRepository


class MentorRepository(AbstractMentorRepository):
    _MESSAGES_TTL_SECONDS = 30 * 24 * 60 * 60
    _FOCUS_TTL_SECONDS = 14 * 24 * 60 * 60

    def __init__(self, store: KeyValueStore):
        self._store = store

    async def get_messages(self, user_id: int) -> list[MentorMessage]:
        raw_messages = await self._store.get_json(self._messages_key(user_id)) or []
        messages: list[MentorMessage] = []
        for item in raw_messages:
            created_at_raw = str(item.get("created_at") or "")
            try:
                created_at = datetime.fromisoformat(created_at_raw)
            except ValueError:
                created_at = datetime.utcnow()
            messages.append(
                MentorMessage(
                    role=str(item.get("role") or "assistant"),
                    content=str(item.get("content") or "").strip(),
                    created_at=created_at,
                    action_steps=[
                        str(step).strip()
                        for step in item.get("action_steps") or []
                        if str(step).strip()
                    ],
                )
            )
        return messages

    async def save_messages(self, user_id: int, messages: list[MentorMessage]) -> None:
        payload = [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "action_steps": list(message.action_steps),
            }
            for message in messages
        ]
        await self._store.set_json(
            self._messages_key(user_id),
            payload,
            expire_seconds=self._MESSAGES_TTL_SECONDS,
        )

    async def get_focus(self, user_id: int) -> MentorFocus | None:
        raw_focus = await self._store.get_json(self._focus_key(user_id))
        if not raw_focus:
            return None
        return MentorFocus(
            key=str(raw_focus.get("key") or "").strip(),
            title=str(raw_focus.get("title") or "").strip(),
            note=str(raw_focus.get("note") or "").strip(),
            track=str(raw_focus.get("track") or "language").strip() or "language",
        )

    async def set_focus(self, user_id: int, focus: MentorFocus | None) -> None:
        if focus is None:
            await self._store.delete(self._focus_key(user_id))
            return
        await self._store.set_json(
            self._focus_key(user_id),
            {
                "key": focus.key,
                "title": focus.title,
                "note": focus.note,
                "track": focus.track,
            },
            expire_seconds=self._FOCUS_TTL_SECONDS,
        )

    @staticmethod
    def _messages_key(user_id: int) -> str:
        return f"mentor:messages:{user_id}"

    @staticmethod
    def _focus_key(user_id: int) -> str:
        return f"mentor:focus:{user_id}"
