"""Порт сборщика PDF-документов."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.application.dto.learning import TrackCardDTO
from src.domain.value_objects.track_type import TrackType


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
        pass
