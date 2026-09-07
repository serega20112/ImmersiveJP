from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects import DocumentTitle, Timestamp, UserDocumentID, UserID


@dataclass
class UserDocument:
    """Доменная модель пользовательского конспекта."""

    user_id: UserID
    title: DocumentTitle
    content: str
    created_at: Timestamp
    id: UserDocumentID | None = None
