from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects import (
    BatchNumber,
    CardPosition,
    LearningCardID,
    Timestamp,
    TrackType,
    UserID,
)


@dataclass
class LearningCard:
    """Доменная модель учебной карточки."""

    user_id: UserID
    track: TrackType
    topic: str
    explanation: str
    created_at: Timestamp
    id: LearningCardID | None = None
    examples: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    batch_number: BatchNumber = BatchNumber(1)
    position: CardPosition = CardPosition(1)

    @classmethod
    def create(
        cls,
        user_id: UserID | int,
        track: TrackType,
        topic: str,
        explanation: str,
        examples: list[str],
        key_terms: list[str],
        batch_number: BatchNumber | int,
        position: CardPosition | int,
        *,
        card_id: LearningCardID | int | None = None,
        created_at: Timestamp | None = None,
    ) -> LearningCard:
        """Создаёт новую учебную карточку.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            topic: Тема карточки.
            explanation: Объяснение темы.
            examples: Примеры использования.
            key_terms: Ключевые термины.
            batch_number: Номер батча.
            position: Позиция в батче.
            card_id: Существующий ID при обновлении карточки.
            created_at: Время создания; по умолчанию текущий момент.

        Returns:
            Новая учебная карточка. ID назначается при сохранении в БД.
        """
        resolved_id = None
        if card_id is not None:
            resolved_id = card_id if isinstance(card_id, LearningCardID) else LearningCardID(card_id)
        return cls(
            id=resolved_id,
            user_id=user_id if isinstance(user_id, UserID) else UserID(user_id),
            track=track,
            topic=topic,
            explanation=explanation,
            examples=examples,
            key_terms=key_terms,
            batch_number=(
                batch_number if isinstance(batch_number, BatchNumber) else BatchNumber(batch_number)
            ),
            position=(
                position if isinstance(position, CardPosition) else CardPosition(position)
            ),
            created_at=created_at or Timestamp.now(),
        )

    def preview(self, max_length: int = 170) -> str:
        """Возвращает краткое описание карточки.

        Args:
            max_length: Максимальная длина превью.

        Returns:
            Обрезанное описание.
        """
        compact = " ".join(self.explanation.split())
        if len(compact) <= max_length:
            return compact
        truncated = compact[: max_length - 1].rsplit(" ", maxsplit=1)[0].strip()
        if not truncated:
            truncated = compact[: max_length - 1].strip()
        return f"{truncated}..."
