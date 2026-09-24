"""Проверить целостность и изоляцию заготовочного контента.

Текст заготовок переехал из кода в JSON, и вместе с переездом появились два новых
риска: файл могут удалить или испортить, а загруженные один раз данные начинают
жить в кэше. Если вызывающий код получает список из кэша и правит его, следующая
партия того же пользователя уже содержит мусор от предыдущей.

Запуск:
    python -m scripts.check_fallback_content
"""

from __future__ import annotations

from src.domain.value_objects.track_type import TrackType
from src.infrastructures.external.llm import fallback_content
from src.infrastructures.external.llm.client import HuggingFaceLLMClient
from src.infrastructures.external.llm.fallback_content import (
    REQUIRED_TRACKS,
    SCENE_FIELDS,
    FallbackContentError,
    card_library,
    default_language_scene,
    ensure_available,
    language_scenes,
)

MIN_CARDS_PER_TRACK = 5
failures: list[str] = []


def report(name: str, ok: bool, detail: str = "") -> None:
    """Зарегистрировать результат проверки.

    Args:
        name: Что проверялось.
        ok: Пройдена ли проверка.
        detail: Пояснение для вывода.
    """
    status = "ok  " if ok else "FAIL"
    print(f"{status} {name} {detail}".rstrip())
    if not ok:
        failures.append(name)


def check_content_loads() -> None:
    """Убедиться, что контент читается, полон и покрыт по всем трекам."""
    try:
        ensure_available()
    except FallbackContentError as error:
        report("контент доступен", False, f"({error})")
        return

    report("контент доступен", True)
    library = card_library()
    missing = [track for track in REQUIRED_TRACKS if track not in library]
    report("все обязательные треки на месте", not missing, f"(нет {missing})" if missing else "")

    for track in REQUIRED_TRACKS:
        cards = library.get(track, ())
        report(
            f"карточек в {track} достаточно",
            len(cards) >= MIN_CARDS_PER_TRACK,
            f"({len(cards)})",
        )

    scene_count = len(language_scenes())
    report("сцены языка загружены", scene_count > 0, f"({scene_count})")
    report(
        "запасная сцена полная",
        set(default_language_scene()) == set(SCENE_FIELDS),
    )


def check_loaders_reject_bad_data() -> None:
    """Убедиться, что битые данные отклоняются, а не проходят молча."""
    cases = (
        ("пустая строка в тексте", lambda: fallback_content._text("  ", where="t")),
        ("не строка в тексте", lambda: fallback_content._text(7, where="t")),
        ("не список в перечислении", lambda: fallback_content._text_list("x", where="t")),
        ("строка с пробелами в списке", lambda: fallback_content._text_list([" ", "a"], where="t")),
        (
            "сцена без обязательных частей",
            lambda: fallback_content._scene_parts({"request_jp": "a"}, where="t"),
        ),
    )
    for name, call in cases:
        try:
            call()
        except FallbackContentError:
            report(f"отклонено: {name}", True)
            continue
        report(f"отклонено: {name}", False, "(ошибка не поднялась)")


def check_cache_is_isolated_from_results() -> None:
    """Проверить, что правка результата не трогает кэш загрузчика."""
    payload = {
        "track": TrackType.LANGUAGE.value,
        "batch_size": 3,
        "batch_number": 1,
        "interests": ["музыка"],
        "previous_topics": [],
    }
    first = HuggingFaceLLMClient._fallback_cards(payload, set(), set())
    report("первая заготовочная партия собрана", len(first) == 3, f"({len(first)})")

    for draft in first:
        draft.examples.append("Мусор из предыдущей партии")
        draft.key_terms.append("Мусор")

    second = HuggingFaceLLMClient._fallback_cards(payload, set(), set())
    report(
        "кэш не протёк во вторую партию",
        all("Мусор" not in " ".join(draft.examples + draft.key_terms) for draft in second),
        f"(примеры {[len(draft.examples) for draft in second]})",
    )

    cached_examples = card_library()[TrackType.LANGUAGE.value][0].examples
    report(
        "кэш остался чистым",
        not any("Мусор" in item for item in cached_examples),
        f"(в кэше {len(cached_examples)} примеров)",
    )


def main() -> int:
    """Прогнать все проверки контента.

    Returns:
        Код завершения: 0 — целостность подтверждена.
    """
    check_content_loads()
    check_loaders_reject_bad_data()
    check_cache_is_isolated_from_results()

    if failures:
        print(f"RESULT: {len(failures)} ПРОБЛЕМ: {', '.join(failures)}")
        return 1
    print("RESULT: FALLBACK CONTENT INTACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
