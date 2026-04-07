from __future__ import annotations

from src.backend.domain.progress import TrackProgressSnapshot
from src.backend.domain.user import SkillAssessment
from src.backend.dto.profile_dto import TrustComponentDTO, TrustScoreDTO


def build_trust_score(
    assessment: SkillAssessment | None,
    snapshots: list[TrackProgressSnapshot],
    total_completed: int,
    total_generated: int,
) -> TrustScoreDTO:
    diagnostic_points = min(40, max(0, int((assessment.score if assessment else 0) * 8)))
    completion_points = (
        min(35, round((total_completed / total_generated) * 35))
        if total_generated
        else 0
    )
    completed_batches = sum(item.completed_batches for item in snapshots)
    stability_points = min(15, completed_batches * 5)

    active_tracks = [item for item in snapshots if item.generated_cards > 0]
    if len(active_tracks) >= 2:
        spread = max(item.completion_rate for item in active_tracks) - min(
            item.completion_rate for item in active_tracks
        )
        balance_points = max(0, 10 - round(spread / 12))
    elif active_tracks:
        balance_points = 8
    else:
        balance_points = 0

    unfinished_tracks = sum(
        1 for item in active_tracks if item.completed_cards < item.generated_cards
    )
    debt_penalty = min(20, unfinished_tracks * 4)

    score = max(
        0,
        min(
            100,
            diagnostic_points
            + completion_points
            + stability_points
            + balance_points
            - debt_penalty,
        ),
    )
    band_key, band_title, summary = _band_for_score(score)
    return TrustScoreDTO(
        score=score,
        band_key=band_key,
        band_title=band_title,
        summary=summary,
        note="Счет может расти и падать. Если новые партии остаются незакрытыми, доверие системы снижается.",
        components=[
            TrustComponentDTO(
                label="Диагностика",
                score=diagnostic_points,
                note="Стартовая база по короткому тесту и самооценке.",
            ),
            TrustComponentDTO(
                label="Закрытые карточки",
                score=completion_points,
                note="Сколько уже пройдено относительно всего материала.",
            ),
            TrustComponentDTO(
                label="Стабильность",
                score=stability_points,
                note="Завершенные партии без долгов по предыдущим блокам.",
            ),
            TrustComponentDTO(
                label="Баланс",
                score=balance_points,
                note="Насколько ровно держатся язык, культура и история.",
            ),
            TrustComponentDTO(
                label="Долг по партиям",
                score=-debt_penalty,
                note="Штраф за новые партии, которые пока не закрыты.",
            ),
        ],
    )


def _band_for_score(score: int) -> tuple[str, str, str]:
    if score < 40:
        return (
            "starter",
            "Новичок",
            "Система пока видит стартовый уровень. Нужна стабильность на карточках и в контрольных работах.",
        )
    if score < 70:
        return (
            "reader",
            "Чтение и письмо",
            "Система уже доверяет знакомому материалу в чтении и письме, но речи еще нужна опора на практику.",
        )
    if score < 90:
        return (
            "speaker",
            "Речь и понимание",
            "Система видит, что язык начинает работать в коротких ответах, бытовых сценах и диалогах.",
        )
    return (
        "fluent",
        "Практическая свобода",
        "Система считает, что базовое практическое использование закреплено и держится без сильной просадки.",
    )
