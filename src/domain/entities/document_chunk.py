"""Фрагмент документа для векторного поиска."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DocumentChunk:
    """Фрагмент документа, подготовленный к векторному поиску."""

    document_id: int | None
    text: str
