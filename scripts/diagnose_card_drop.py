"""Диагностика: сколько карточек доживает до пользователя.

Прогоняет правдоподобный ответ модели через реальный _normalize_cards и
показывает, на каком фильтре карточка теряется. Нужен, потому что фолбэк
молча подменяет отбракованные карточки, и по одному лишь HTTP-ответу не видно,
что модель отработала, а фильтр выбросил.

Использование (из корня репозитория):
    python -m scripts.diagnose_card_drop
"""

from __future__ import annotations

from src.infrastructures.external.llm.client import HuggingFaceLLMClient


def language_response() -> list[dict]:
    """Собрать ответ модели для трека language.

    Returns:
        Пять карточек с японскими примерами.
    """
    return [
        {
            "topic": "Заказ кофе в киосске",
            "explanation": "Просим через ください, коротко и вежливо.",
            "examples": ["コーヒーをください | koohii o kudasai | Кофе, пожалуйста"],
            "key_terms": ["コーヒー | кофе", "ください | пожалуйста", "店 | магазин"],
        },
        {
            "topic": "Как спросить цену",
            "explanation": "Вопрос про цену через いくら.",
            "examples": ["いくらですか | ikura desu ka | Сколько это стоит?"],
            "key_terms": ["いくら | сколько", "です | есть", " yen | йена"],
        },
        {
            "topic": "Извинение в толпе",
            "explanation": "-sumimasen закрывает и извинение, и просьбу.",
            "examples": ["ごめんなさい | gomen nasai | Простите"],
            "key_terms": ["ごめんなさい | простите", "すみません | извините"],
        },
        {
            "topic": "Прощание в разговоре",
            "explanation": "Завершаем реплику по форме.",
            "examples": ["またあした | mata ashita | До завтра"],
            "key_terms": ["また | снова", "あした | завтра"],
        },
        {
            "topic": "Обозначаем направление",
            "explanation": "Частица へ даёт направление движения.",
            "examples": ["東京へ行きます | toukyou e ikimasu | Еду в Токио"],
            "key_terms": ["へ | в", "東京 | Токио", "行きます | идти"],
        },
    ]


def culture_response() -> list[dict]:
    """Собрать ответ модели для трека culture.

    Возвращает заведомо корректные карточки по культуре, но без прямых
    вхождений слов из стоп-стеблей фильтра — так видно, режет ли их лексика.

    Returns:
        Пять карточек о повседневных нормах.
    """
    return [
        {
            "topic": "Снимать обувь у порога",
            "explanation": "Гость оставляет обувь снаружи и надевает тапочки.",
            "examples": [],
            "key_terms": ["うわばき | сменная обувь", "げんかん | прихожая"],
        },
        {
            "topic": "Поклон при встрече",
            "explanation": "Глубина поклона зависит от того, с кем здороваются.",
            "examples": [],
            "key_terms": ["おじぎ | поклон", "あいさつ | приветствие"],
        },
        {
            "topic": "Тихо в вагоне поезда",
            "explanation": "Разговор по телефону в электричке считается дурным тоном.",
            "examples": [],
            "key_terms": ["でんしゃ | поезд", "しずか | тихо"],
        },
        {
            "topic": "Чаевые не оставляют",
            "explanation": "В кафе лишний деньги кладут на стол не как благодарность.",
            "examples": [],
            "key_terms": ["チップ | чаевые", "れいほう | вознаграждение"],
        },
        {
            "topic": "Очередь к входу",
            "explanation": "Люди ждут groups по одному, не толкаясь.",
            "examples": [],
            "key_terms": ["きょうこう | вход", "ならぶ | стоять в очереди"],
        },
    ]


def history_response() -> list[dict]:
    """Собрать ответ модели для трека history.

    Returns:
        Пять карточек о исторических сюжетах.
    """
    return [
        {
            "topic": "Пожар 1923 года",
            "explanation": "После землетрясения город отстраивали заново.",
            "examples": [],
            "key_terms": ["じしん | землетрясение", "ふっかつ | восстановление"],
        },
        {
            "topic": "Дворец в Киото",
            "explanation": "Императорский двор переехал вместе со столицей.",
            "examples": [],
            "key_terms": ["きょうと | Киото", "みやこ | столица"],
        },
        {
            "topic": "Печать и торговля",
            "explanation": "Власть выдавала разрешения на морские поездки.",
            "examples": [],
            "key_terms": ["とぎょ | торговля", "ふね | корабль"],
        },
        {
            "topic": "Школьная реформа",
            "explanation": "Новая программа обучения появилась в конце века.",
            "examples": [],
            "key_terms": ["school | школа", "せいど | устройство"],
        },
        {
            "topic": "Город после войны",
            "explanation": "Улицы отстроили по другому плану.",
            "examples": [],
            "key_terms": ["まち | город", "ふくごう | восстановление"],
        },
    ]


def off_track_response() -> tuple[str, list[dict]]:
    """Собрать карточки, которые правильно должны быть отбракованы.

    Возвращает заведомо чужой материал для трека culture: карточку про грамматику
    и карточку про историю эпохи. Если после смягчения фильтра они начинают
    проходить — защита просто выключена, и это регресс.

    Returns:
        Кортеж ключа трека и списка карточек.
    """
    return (
        "culture",
        [
            {
                "topic": "Граматика частиц は и が",
                "explanation": "Разбираем грамматика: частица маркирует тему, ромадзи помогает чтению.",
                "examples": ["私は学生です | watashi wa gakusei desu | Я студент"],
                "key_terms": ["は | тема", "が | субъект", "частиц | правило"],
            },
            {
                "topic": "Реформы эпохи Мэйдзи",
                "explanation": "Исторический перелом: после реставрации императорской власти началась модернизация государства.",
                "examples": [],
                "key_terms": ["めいじ | Мэйдзи", "歴史 | история", "改革 | реформа"],
            },
        ],
    )


CASES: dict[str, list[dict]] = {
    "language": language_response(),
    "culture": culture_response(),
    "history": history_response(),
}


def report_track(track: str, parsed: list[dict]) -> None:
    """Показать, сколько карточек выжило и почему отбракованы остальные.

    Args:
        track: Ключ трека обучения.
        parsed: Ответ модели для этого трека.
    """
    payload = {"track": track, "batch_size": 5, "interests": [], "goal": "daily"}
    before = {item["topic"] for item in parsed}
    batch = HuggingFaceLLMClient._normalize_cards(parsed, payload)
    kept = {draft.topic for draft in batch.drafts}

    generated_from_model = [topic for topic in before if topic in kept]
    print(f"--- track={track} ---")
    print(f"  модель отдала карточек      : {len(before)}")
    print(f"  прошло фильтр               : {len(generated_from_model)}")
    print(f"  итог в партии               : {len(batch.drafts)}")
    print(f"  от модели по разделению     : {batch.model_count}")
    print(f"  добрано из фолбэка          : {batch.fallback_count}")
    for topic in sorted(before - kept):
        item = next(entry for entry in parsed if entry["topic"] == topic)
        examples = HuggingFaceLLMClient._normalize_card_examples(item.get("examples") or [])
        matches = HuggingFaceLLMClient._card_matches_track(
            track=track,
            topic=topic,
            explanation=item.get("explanation", ""),
            examples=examples,
            key_terms=item.get("key_terms") or [],
        )
        placeholder = HuggingFaceLLMClient._is_placeholder_topic(topic)
        reason = "не проходит проверку трека" if not matches else "иное"
        print(f"    ОТБРАКОВАНА: {topic} -> {reason} (placeholder={placeholder})")
    print()


def main() -> None:
    """Прогнать все треки, напечатать сводку и проверить отсев чужого."""
    print("Партия = 5 карточек, модель отвечает полностью и корректно.\n")
    for track, parsed in CASES.items():
        report_track(track, parsed)

    track, off_track = off_track_response()
    payload = {"track": track, "batch_size": len(off_track), "interests": [], "goal": "daily"}
    batch = HuggingFaceLLMClient._normalize_cards(off_track, payload)
    survivors = [
        draft.topic
        for draft in batch.drafts
        if draft.topic in {item["topic"] for item in off_track}
    ]
    print(f"--- track={track} (заведомо чужие карточки) ---")
    print(f"  подано на проверку          : {len(off_track)}")
    print(f"  прошло (должно быть 0)      : {len(survivors)}")
    for topic in survivors:
        print(f"    ПРОПУЩЕНО: {topic}")


if __name__ == "__main__":
    main()
