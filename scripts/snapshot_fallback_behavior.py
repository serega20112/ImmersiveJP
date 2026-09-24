"""Снять или сравнить поведение заготовочного контента.

Вынос учебного текста из кода в данные не должен поменять ни одной карточки:
пользователь, у которого модель недоступна, обязан получить ровно тот же
материал, что и раньше. Снимок берётся ДО переделки и сверяется ПОСЛЕ.

Запуск:
    python -m scripts.snapshot_fallback_behavior --save
    python -m scripts.snapshot_fallback_behavior --check
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.domain.value_objects.track_type import TrackType
from src.infrastructures.external.llm.client import HuggingFaceLLMClient

SNAPSHOT_PATH = Path("build/fallback_behavior_snapshot.json")
TRACKS = [TrackType.LANGUAGE, TrackType.CULTURE, TrackType.HISTORY]
SCENE_TITLES = [
    "Кафе и заказы",
    "Поход на станцию",
    "Магазин и оплата",
    "Университет и задания",
    "Офисная переписка",
    "Жильё и договор",
    "Клиника и лекарства",
    "Улица и маршрут",
    "Что-то совсем другое",
    "",
]


def card_payload(track: TrackType, batch_size: int, excluded: tuple[str, ...]) -> dict:
    """Собрать контекст генерации для заготовочной партии.

    Args:
        track: Тип трека.
        batch_size: Размер партии.
        excluded: Темы, которые нужно пропустить.

    Returns:
        Payload для _fallback_cards.
    """
    return {
        "track": track.value,
        "batch_size": batch_size,
        "batch_number": 1,
        "interests": ["аниме", "готовку"],
        "language_level": "beginner",
        "goal": "travel",
        "study_timeline": "one_month",
        "diagnostic_level": "A1",
        "diagnostic_summary": "короткая сводка",
        "strengths": ["Чтение", "Лексика"],
        "weak_points": ["Кандзи", "Грамматика", "Хирагана", "Аудирование", "Произношение"],
        "excluded_topics": list(excluded),
    }


def collect_cards() -> list[dict]:
    """Прогнать заготовочную генерацию карточек по всем комбинациям.

    Returns:
        Список результатов в стабильном порядке.
    """
    results: list[dict] = []
    exclusions: list[tuple[str, ...]] = [(), ("Приветствия без учебниковой скуки",)]
    for track in TRACKS:
        for batch_size in (1, 2, 3, 4, 5, 7):
            for excluded in exclusions:
                payload = card_payload(track, batch_size, excluded)
                drafts = HuggingFaceLLMClient._fallback_cards(
                    payload,
                    {item.casefold() for item in excluded},
                    set(),
                )
                results.append(
                    {
                        "case": f"{track.value}/{batch_size}/{len(excluded)}",
                        "drafts": [draft.model_dump() for draft in drafts],
                    }
                )
    return results


def collect_scenes() -> list[dict]:
    """Собрать выборку языковых сцен по заголовкам контекста.

    Returns:
        Список соответствий заголовок -> набор частей сцены.
    """
    return [
        {"title": title, "scene": HuggingFaceLLMClient._language_scene_parts(title)}
        for title in SCENE_TITLES
    ]


def collect_dynamic_cards() -> list[dict]:
    """Собрать динамические заготовочные карточки по всем трекам.

    Returns:
        Список результатов в стабильном порядке.
    """
    results: list[dict] = []
    interests_options = ["аниме, готовить", "живой контекст"]
    for track in TRACKS:
        for interests in interests_options:
            payload = card_payload(track, 5, ())
            drafts = HuggingFaceLLMClient._build_dynamic_fallback_cards(
                payload=payload,
                interests=interests,
                excluded_topics=set(),
                excluded_example_signatures=set(),
            )
            results.append(
                {
                    "case": f"{track.value}/{interests}",
                    "drafts": [draft.model_dump() for draft in drafts],
                }
            )
    return results


def build_snapshot() -> dict:
    """Собрать полный снимок поведения заготовок.

    Returns:
        Снимок для записи или сравнения.
    """
    return {
        "cards": collect_cards(),
        "scenes": collect_scenes(),
        "dynamic_cards": collect_dynamic_cards(),
    }


def main(argv: list[str] | None = None) -> int:
    """Сохранить или сверить снимок поведения.

    Args:
        argv: Аргументы командной строки.

    Returns:
        Код завершения: 0 — поведение совпало либо снимок сохранён.
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--save", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    snapshot = build_snapshot()

    if args.save:
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"снимок сохранён: {SNAPSHOT_PATH}")
        print(f"карточек: {len(snapshot['cards'])}, сцен: {len(snapshot['scenes'])}")
        return 0

    if not SNAPSHOT_PATH.exists():
        print("FAIL снимок не найден, сначала запусти --save")
        return 1

    previous = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    rendered_new = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    rendered_old = json.dumps(previous, ensure_ascii=False, sort_keys=True)

    if rendered_new == rendered_old:
        print(
            f"совпало полностью: карточек {len(snapshot['cards'])}, "
            f"сцен {len(snapshot['scenes'])}, динамических {len(snapshot['dynamic_cards'])}"
        )
        print("RESULT: IDENTICAL")
        return 0

    print("FAIL поведение заготовок изменилось")
    for section in ("cards", "scenes", "dynamic_cards"):
        for old_item, new_item in zip(
            previous.get(section, []),
            snapshot.get(section, []),
            strict=True,
        ):
            if old_item != new_item:
                key = old_item.get("case") or old_item.get("title")
                print(f"  расхождение в {section}: {key}")
    print("RESULT: MISMATCH")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
