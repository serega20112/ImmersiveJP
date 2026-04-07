from __future__ import annotations

import re

from src.backend.domain.content import LearningCard
from src.backend.domain.progress import TrackProgressSnapshot
from src.backend.domain.user import SkillAssessment, User
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.dto.learning_dto import CardExampleDTO, TrackCardDTO
from src.backend.dto.profile_dto import TrackProgressDTO
from src.backend.dto.skill_dto import SkillAssessmentDTO
from src.backend.use_case.key_terms import build_key_term_dtos


_LEVEL_TITLES = {
    "zero": "Стартовый",
    "basic": "Базовый",
    "intermediate": "Уверенный",
}


def to_user_view_dto(user: User) -> UserViewDTO:
    return UserViewDTO(
        id=int(user.id or 0),
        email=user.email,
        display_name=user.display_name,
        is_email_verified=user.is_email_verified,
        onboarding_completed=user.onboarding_completed,
        learning_goal=user.learning_goal.value if user.learning_goal else None,
        language_level=user.language_level.value if user.language_level else None,
        study_timeline=user.study_timeline.value if user.study_timeline else None,
        interests=list(user.interests),
    )


def to_track_card_dto(card: LearningCard, completed_ids: set[int]) -> TrackCardDTO:
    cleaned_explanation = _sanitize_generated_note(card.explanation)
    return TrackCardDTO(
        id=int(card.id or 0),
        track=card.track.value,
        topic=card.topic,
        preview=_build_preview(cleaned_explanation),
        explanation=cleaned_explanation,
        examples=[_to_card_example_dto(example) for example in card.examples],
        key_terms=list(card.key_terms),
        key_term_items=build_key_term_dtos(card.key_terms),
        batch_number=card.batch_number,
        position=card.position,
        is_completed=int(card.id or 0) in completed_ids,
    )


def to_track_progress_dto(snapshot: TrackProgressSnapshot) -> TrackProgressDTO:
    return TrackProgressDTO(
        track=snapshot.track.value,
        title=snapshot.track.title,
        completed_cards=snapshot.completed_cards,
        generated_cards=snapshot.generated_cards,
        current_batch=snapshot.current_batch,
        completion_rate=snapshot.completion_rate,
        completed_batches=snapshot.completed_batches,
        work_ready_batch=snapshot.work_ready_batch,
    )


def to_skill_assessment_dto(
    assessment: SkillAssessment | None,
) -> SkillAssessmentDTO | None:
    if assessment is None or assessment.estimated_level is None:
        return None
    return SkillAssessmentDTO(
        score=assessment.score,
        estimated_level=assessment.estimated_level.value,
        estimated_level_title=_LEVEL_TITLES.get(assessment.estimated_level.value),
        summary=assessment.summary,
        strengths=list(assessment.strengths),
        weak_points=list(assessment.weak_points),
    )


def _build_preview(text: str, max_length: int = 170) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    truncated = compact[: max_length - 1].rsplit(" ", maxsplit=1)[0].strip()
    if not truncated:
        truncated = compact[: max_length - 1].strip()
    return f"{truncated}..."


def _sanitize_generated_note(text: str) -> str:
    compact = " ".join((text or "").split())
    if not compact:
        return ""

    replacements = {
        "'tourism'": "'туризм'",
        "'relocation'": "'переезд'",
        "'work'": "'работа'",
        "'university'": "'университет'",
        "'zero'": "'стартовый'",
        "'basic'": "'базовый'",
        "'intermediate'": "'уверенный'",
        "trust score": "оценка прогресса",
    }
    for source, target in replacements.items():
        compact = compact.replace(source, target)

    word_replacements = {
        r"\btourism\b": "туризм",
        r"\brelocation\b": "переезд",
        r"\bwork\b": "работа",
        r"\buniversity\b": "университет",
        r"\bzero\b": "стартовый",
        r"\bbasic\b": "базовый",
        r"\bintermediate\b": "уверенный",
        r"\btrust score\b": "оценка прогресса",
    }
    for pattern, replacement in word_replacements.items():
        compact = re.sub(pattern, replacement, compact, flags=re.IGNORECASE)

    compact = re.sub(r"Эта карточка про тему '[^']+'\.\s*", "", compact, flags=re.IGNORECASE)

    sentences = re.split(r"(?<=[.!?])\s+", compact)
    filtered = [sentence.strip() for sentence in sentences if not _is_noise_sentence(sentence)]
    normalized = " ".join(filtered).strip()
    return normalized or compact


def _is_noise_sentence(sentence: str) -> bool:
    normalized = sentence.casefold()
    noise_fragments = (
        "смотри на тему",
        "эта карточка про тему",
        "диагностика пользователя",
        "быстрый тест:",
        "самооценка:",
        "текущий старт",
        "в расчет",
        "лучше всего держатся",
        "проседают",
        "под цель",
        "для уровня",
        "оценка прогресса",
        "цель:",
        "уровень:",
        "сильные стороны",
        "слабые стороны",
    )
    return any(fragment in normalized for fragment in noise_fragments)


def _to_card_example_dto(example: str) -> CardExampleDTO:
    parts = [part.strip() for part in example.split("|")]
    if len(parts) >= 3:
        japanese, romaji, translation = parts[:3]
        return CardExampleDTO(
            raw_text=example,
            japanese=japanese,
            romaji=romaji,
            translation=translation,
        )
    if len(parts) == 2:
        japanese, translation = parts
        return CardExampleDTO(
            raw_text=example,
            japanese=japanese,
            translation=translation,
        )
    return CardExampleDTO(raw_text=example, japanese=example)
