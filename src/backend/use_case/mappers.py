from __future__ import annotations

from src.backend.domain.content import LearningCard
from src.backend.domain.progress import TrackProgressSnapshot
from src.backend.domain.user import User
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.dto.learning_dto import CardExampleDTO, TrackCardDTO
from src.backend.dto.profile_dto import TrackProgressDTO


def to_user_view_dto(user: User) -> UserViewDTO:
    return UserViewDTO(
        id=int(user.id or 0),
        email=user.email,
        display_name=user.display_name,
        is_email_verified=user.is_email_verified,
        onboarding_completed=user.onboarding_completed,
        learning_goal=user.learning_goal.value if user.learning_goal else None,
        language_level=user.language_level.value if user.language_level else None,
        interests=list(user.interests),
    )


def to_track_card_dto(card: LearningCard, completed_ids: set[int]) -> TrackCardDTO:
    return TrackCardDTO(
        id=int(card.id or 0),
        track=card.track.value,
        topic=card.topic,
        preview=_build_preview(card.explanation),
        explanation=card.explanation,
        examples=[_to_card_example_dto(example) for example in card.examples],
        key_terms=list(card.key_terms),
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
    )


def _build_preview(text: str, max_length: int = 170) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    truncated = compact[: max_length - 1].rsplit(" ", maxsplit=1)[0].strip()
    if not truncated:
        truncated = compact[: max_length - 1].strip()
    return f"{truncated}..."


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
