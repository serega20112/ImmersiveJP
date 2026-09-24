"""Фабрики DTO прогресса: оценка прогресса и вложенные компоненты."""

from __future__ import annotations

from src.application.dto.profile import TrustComponentDTO, TrustScoreDTO


def build_trust_score(
    score: int = 70,
    band_key: str = "steady",
    band_title: str = "Уверенно",
    *,
    summary: str = "Хороший темп",
    note: str = "Продолжай",
) -> TrustScoreDTO:
    """Собрать корректную оценку прогресса с одним компонентом.

    Args:
        score: Итоговый балл оценки.
        band_key: Машинный ключ диапазона оценки.
        band_title: Название диапазона оценки.
        summary: Текстовое резюме оценки.
        note: Короткая заметка к оценке.

    Returns:
        DTO оценки прогресса, пригодный для вложенных DTO.
    """
    return TrustScoreDTO(
        score=score,
        band_key=band_key,
        band_title=band_title,
        summary=summary,
        note=note,
        components=[TrustComponentDTO(label="Карточки", score=score, note="Норма")],
    )
