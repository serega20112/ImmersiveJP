from __future__ import annotations

import re

from src.application.dto.auth import UserViewDTO
from src.application.dto.learning import (
    CardExampleDTO,
    PreparedWorkTaskDTO,
    TrackCardDTO,
    TrackWorkTaskDTO,
)
from src.application.dto.profile import TrackProgressDTO
from src.application.dto.skill import SkillAssessmentDTO
from src.application.use_cases.card_example import parse_example
from src.application.use_cases.key_terms import build_key_term_dtos
from src.domain.aggregates.user import User
from src.domain.entities.content import LearningCard
from src.domain.entities.progress import TrackProgressSnapshot
from src.domain.value_objects.skill_assessment import SkillAssessment

_LEVEL_TITLES = {
    "zero": "Стартовый",
    "basic": "Базовый",
    "intermediate": "Уверенный",
}


def to_user_view_dto(user: User) -> UserViewDTO:
    """Convert a User entity to a UserViewDTO.

    Args:
        user: The user entity.

    Returns:
        The user view DTO.
    """
    return UserViewDTO(
        id=int(user.id) if user.id is not None else 0,
        email=str(user.email),
        display_name=str(user.display_name),
        is_email_verified=user.is_email_verified,
        onboarding_completed=user.onboarding_completed,
        learning_goal=user.learning_goal.value if user.learning_goal else None,
        language_level=user.language_level.value if user.language_level else None,
        study_timeline=user.study_timeline.value if user.study_timeline else None,
        interests=list(user.interests),
    )


def to_track_card_dto(card: LearningCard, completed_ids: set[int]) -> TrackCardDTO:
    """Convert a LearningCard to a TrackCardDTO.

    Args:
        card: The learning card entity.
        completed_ids: Set of completed card IDs.

    Returns:
        The track card DTO.
    """
    cleaned_explanation = _sanitize_generated_note(card.explanation)
    card_id = int(card.id) if card.id is not None else 0
    return TrackCardDTO(
        id=card_id,
        track=card.track.value,
        topic=card.topic,
        preview=_build_preview(cleaned_explanation),
        explanation=cleaned_explanation,
        examples=[_to_card_example_dto(example) for example in card.examples],
        key_terms=list(card.key_terms),
        key_term_items=build_key_term_dtos(card.key_terms),
        batch_number=int(card.batch_number),
        position=int(card.position),
        is_completed=card_id in completed_ids,
    )


def to_track_progress_dto(snapshot: TrackProgressSnapshot) -> TrackProgressDTO:
    """Convert a TrackProgressSnapshot to a TrackProgressDTO.

    Args:
        snapshot: The track progress snapshot.

    Returns:
        The track progress DTO.
    """
    return TrackProgressDTO(
        track=snapshot.track.value,
        title=snapshot.track.title,
        completed_cards=int(snapshot.completed_cards.value),
        generated_cards=int(snapshot.generated_cards.value),
        current_batch=snapshot.current_batch,
        completion_rate=float(snapshot.completion_rate.percentage),
        completed_batches=snapshot.completed_batches,
        work_ready_batch=snapshot.work_ready_batch,
    )


def to_skill_assessment_dto(
    assessment: SkillAssessment | None,
) -> SkillAssessmentDTO | None:
    """Преобразовать оценку навыков в DTO для показа.

    Args:
        assessment: Доменная оценка навыков либо None.

    Returns:
        DTO оценки навыков либо None, если оценки нет.
    """
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


def to_track_work_task_dto(
    task: PreparedWorkTaskDTO,
    submitted_answer: str | None = None,
) -> TrackWorkTaskDTO:
    """Преобразовать подготовленное задание в DTO для показа.

    Args:
        task: Подготовленное задание работы.
        submitted_answer: Ответ пользователя, если он уже известен.

    Returns:
        DTO задания для страницы работы.
    """
    return TrackWorkTaskDTO(
        id=task.id,
        kind=task.kind,
        title=task.title,
        prompt=task.prompt,
        expected_format=task.expected_format,
        source_topic=task.source_topic,
        placeholder=task.placeholder,
        required_terms=list(task.required_terms),
        hints=list(task.hints),
        submitted_answer=submitted_answer,
    )


def to_track_work_review_payload(
    task: PreparedWorkTaskDTO,
    submitted_answer: str | None = None,
) -> dict[str, object]:
    """Подготовить описание задания для проверки нейросетью.

    В отличие от DTO для страницы сюда попадают правила засчёта: допустимые
    варианты и порог обязательных элементов. Без них модель не сможет
    отличить зачётный ответ от формально похожего.

    Args:
        task: Подготовленное задание работы.
        submitted_answer: Ответ пользователя, если он уже известен.

    Returns:
        Словарь задания для промпта проверки работы.
    """
    return {
        "id": task.id,
        "kind": task.kind,
        "title": task.title,
        "prompt": task.prompt,
        "expected_format": task.expected_format,
        "source_topic": task.source_topic,
        "required_terms": list(task.required_terms),
        "minimum_term_hits": task.minimum_term_hits,
        "expected_answers": list(task.expected_answers),
        "revealed_answer": task.revealed_answer,
        "answer": str(submitted_answer or "").strip(),
    }


def _build_preview(text: str, max_length: int = 170) -> str:
    """Build a truncated preview of a text.

    Args:
        text: The text to truncate.
        max_length: Maximum length of the preview.

    Returns:
        The truncated preview string.
    """
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    truncated = compact[: max_length - 1].rsplit(" ", maxsplit=1)[0].strip()
    if not truncated:
        truncated = compact[: max_length - 1].strip()
    return f"{truncated}..."


def _sanitize_generated_note(text: str) -> str:
    """Sanitize generated note text by replacing tokens and removing noise.

    Args:
        text: The raw generated text.

    Returns:
        The cleaned text.
    """
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
    """Check if a sentence is noise that should be filtered out.

    Args:
        sentence: The sentence to check.

    Returns:
        True if the sentence is noise.
    """
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
    """Преобразовать строку примера карточки в DTO.

    Args:
        example: Исходная строка примера из карточки.

    Returns:
        DTO разобранного примера.
    """
    parsed = parse_example(example)
    return CardExampleDTO(
        raw_text=example,
        japanese=parsed["japanese"],
        romaji=parsed["romaji"],
        translation=parsed["translation"],
    )
