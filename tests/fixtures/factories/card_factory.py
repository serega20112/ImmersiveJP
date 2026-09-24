"""Фабрика учебной карточки LearningCard для тестов."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.entities.content import LearningCard
from src.domain.value_objects.track_type import TrackType


@dataclass
class CardFactory:
    """Строитель валидной карточки LearningCard с значениями по умолчанию."""

    user_id: int = 1
    track: TrackType = TrackType.LANGUAGE
    topic: str = "私 は 学校 に 行きます"
    explanation: str = "Конструкция 「に行く」 обозначает движение к месту цели."
    examples: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=lambda: ["がっこう", "学校"])
    batch_number: int = 1
    position: int = 1
    card_id: int | None = None

    def build(self) -> LearningCard:
        """Собрать карточку LearningCard из текущих значений фабрики.

        Returns:
            Валидная доменная карточка с заполненными value objects.
        """
        return LearningCard.create(
            user_id=self.user_id,
            track=self.track,
            topic=self.topic,
            explanation=self.explanation,
            examples=list(self.examples),
            key_terms=list(self.key_terms),
            batch_number=self.batch_number,
            position=self.position,
            card_id=self.card_id,
        )
