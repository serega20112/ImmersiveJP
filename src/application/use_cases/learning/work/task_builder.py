"""Сборка заданий работы по завершённой партии карточек."""

from __future__ import annotations

import re

from src.application.dto.learning import PreparedWorkTaskDTO
from src.application.use_cases.card_example import parse_example
from src.application.use_cases.key_terms import key_term_prompt_value
from src.application.use_cases.learning.work.answer_check import normalize_text
from src.domain.entities.content import LearningCard
from src.domain.value_objects.track_type import TrackType

_LANGUAGE_EXAMPLES = 3
_TARGET_TERM_COUNT = 6
_TERMS_PER_TASK = 2
_REVIEW_TERMS_PER_TASK = 1
_CONFIDENCE_TERMS_LIMIT = 3
_LATIN_TERM_PATTERN = re.compile(r"[a-z0-9 _/-]+")
_TERM_STRIP_CHARACTERS = ".,!;:()[]{}\"'`"

WorkExample = dict[str, str | None]


def build_prepared_work_tasks(
    track: TrackType,
    cards: list[LearningCard],
    review_cards: list[LearningCard] | None = None,
) -> list[PreparedWorkTaskDTO]:
    """Собрать задания работы по партии.

    В языковом треке задания строятся вокруг конкретных примеров из карточек:
    чтение, перевод, восстановление фразы, сцена и связка старого материала
    с новым. В культурном и историческом треках примеры не используются —
    опора идёт на темы и ключевые термины карточек.

    Args:
        track: Тип трека обучения.
        cards: Карточки текущей партии.
        review_cards: Карточки предыдущей партии для задания на повторение.

    Returns:
        Список заданий; пустой, если партия не содержит карточек.
    """
    if not cards:
        return []

    current_terms = _collect_terms(track, cards)
    review_terms = _collect_terms(track, review_cards or [])

    if track == TrackType.LANGUAGE:
        return _build_language_tasks(
            cards=cards,
            examples=_select_examples(cards),
            current_terms=current_terms,
            review_terms=review_terms,
        )

    return _build_context_tasks(
        track=track,
        cards=cards,
        current_terms=current_terms,
        review_terms=review_terms,
    )


def _select_examples(cards: list[LearningCard]) -> list[tuple[LearningCard, WorkExample]]:
    """Отобрать до трёх примеров для заданий языковой партии.

    Сначала берётся первый пригодный пример каждой карточки, чтобы задания
    опирались на разные карточки. Если таких меньше трёх, добавляются
    остальные примеры без повторов внутри одной карточки.

    Args:
        cards: Карточки текущей партии.

    Returns:
        Пары карточка и разобранный пример.
    """
    selected: list[tuple[LearningCard, WorkExample]] = []

    for card in cards:
        for example in card.examples:
            parsed = parse_example(example)
            if parsed["japanese"]:
                selected.append((card, parsed))
                break

    if len(selected) >= _LANGUAGE_EXAMPLES:
        return selected

    for card in cards:
        for example in card.examples:
            parsed = parse_example(example)
            if not parsed["japanese"]:
                continue
            if any(
                chosen_card.id == card.id and chosen_example["japanese"] == parsed["japanese"]
                for chosen_card, chosen_example in selected
            ):
                continue
            selected.append((card, parsed))
            if len(selected) >= _LANGUAGE_EXAMPLES:
                return selected

    return selected


def _topic_example(card: LearningCard) -> WorkExample:
    """Подставить тему карточки вместо отсутствующего примера.

    Нужен, когда партия обошлась без пригодных примеров: задание всё равно
    должно строиться на материале карточки, а не исчезать.

    Args:
        card: Карточка, тема которой подставляется в пример.

    Returns:
        Пример, где темой заполнены японская часть и перевод.
    """
    return {"japanese": card.topic, "romaji": None, "translation": card.topic}


def _build_language_tasks(
    *,
    cards: list[LearningCard],
    examples: list[tuple[LearningCard, WorkExample]],
    current_terms: list[str],
    review_terms: list[str],
) -> list[PreparedWorkTaskDTO]:
    """Собрать задания языкового трека.

    Args:
        cards: Карточки текущей партии.
        examples: Отобранные примеры, дополняемые темой первой карточки.
        current_terms: Элементы текущей партии.
        review_terms: Элементы предыдущей партии.

    Returns:
        Пять заданий: чтение, перевод, фраза по памяти, сцена и связка.
    """
    picked = list(examples)
    if not picked:
        picked = [(cards[0], _topic_example(cards[0]))]
    while len(picked) < _LANGUAGE_EXAMPLES:
        picked.append(picked[-1])

    first_card, first_example = picked[0]
    second_card, second_example = picked[1]
    third_card, third_example = picked[2]
    scene_terms = current_terms[:_TERMS_PER_TASK]
    confidence_terms = _confidence_terms(
        scene_terms,
        review_terms[:_REVIEW_TERMS_PER_TASK],
    )

    return [
        PreparedWorkTaskDTO(
            id="reading",
            kind="recall",
            title="Чтение",
            prompt=f"Запиши ромадзи для фразы: {first_example['japanese']}",
            expected_format="ромадзи",
            source_topic=first_card.topic,
            placeholder="Например: watashi wa ...",
            expected_answers=[first_example["romaji"] or ""],
            revealed_answer=first_example["romaji"],
        ),
        PreparedWorkTaskDTO(
            id="meaning",
            kind="recall",
            title="Перевод",
            prompt=f"Переведи на русский: {second_example['japanese']}",
            expected_format="краткий перевод",
            source_topic=second_card.topic,
            placeholder="Например: я иду в школу",
            expected_answers=[second_example["translation"] or ""],
            revealed_answer=second_example["translation"],
        ),
        PreparedWorkTaskDTO(
            id="recall",
            kind="recall",
            title="Фраза по памяти",
            prompt=(
                f"Восстанови фразу по памяти: {third_example['translation'] or third_card.topic}"
            ),
            expected_format="ромадзи или японский",
            source_topic=third_card.topic,
            placeholder="Можно в ромадзи, японская раскладка не обязательна",
            expected_answers=[
                answer for answer in (third_example["japanese"], third_example["romaji"]) if answer
            ],
            revealed_answer=third_example["romaji"] or third_example["japanese"],
        ),
        PreparedWorkTaskDTO(
            id="scene",
            kind="production",
            title="Сцена",
            prompt=_scene_prompt(TrackType.LANGUAGE, scene_terms, cards[0].topic),
            expected_format="1-2 строки, можно в ромадзи",
            source_topic=cards[0].topic,
            placeholder="Напиши короткий ответ. Можно в ромадзи.",
            required_terms=list(scene_terms),
            minimum_term_hits=min(_TERMS_PER_TASK, len(scene_terms)),
            revealed_answer=", ".join(scene_terms),
        ),
        PreparedWorkTaskDTO(
            id="confidence",
            kind="immersion",
            title="Контроль уверенности",
            prompt=_confidence_prompt(
                track=TrackType.LANGUAGE,
                current_topic=cards[-1].topic,
                current_terms=scene_terms,
                review_terms=review_terms[:_REVIEW_TERMS_PER_TASK],
            ),
            expected_format="1-3 строки, можно в ромадзи",
            source_topic=cards[-1].topic,
            placeholder="Соедини старый и новый материал. Можно в ромадзи.",
            required_terms=confidence_terms,
            minimum_term_hits=min(_TERMS_PER_TASK, len(confidence_terms)),
            revealed_answer=", ".join(confidence_terms),
        ),
    ]


def _build_context_tasks(
    *,
    track: TrackType,
    cards: list[LearningCard],
    current_terms: list[str],
    review_terms: list[str],
) -> list[PreparedWorkTaskDTO]:
    """Собрать задания культурного и исторического треков.

    Args:
        track: Тип трека обучения.
        cards: Карточки текущей партии.
        current_terms: Элементы текущей партии.
        review_terms: Элементы предыдущей партии.

    Returns:
        Пять заданий: тезис, контекст, смысл, сцена и связка материала.
    """
    first_card = cards[0]
    second_card = cards[1] if len(cards) > 1 else cards[0]
    third_card = cards[2] if len(cards) > 2 else cards[-1]
    first_terms = _terms_or_topic(current_terms, 0, _TERMS_PER_TASK, first_card.topic)
    second_terms = _terms_or_topic(
        current_terms,
        _TERMS_PER_TASK,
        _TERMS_PER_TASK * 2,
        second_card.topic,
    )
    confidence_terms = _confidence_terms(
        current_terms[:_TERMS_PER_TASK],
        review_terms[:_REVIEW_TERMS_PER_TASK],
    )
    if not confidence_terms:
        confidence_terms = _terms_or_topic(current_terms, 0, _TERMS_PER_TASK, cards[-1].topic)

    return [
        PreparedWorkTaskDTO(
            id="thesis",
            kind="production",
            title="Тезис",
            prompt=(
                f"Собери 1 короткое предложение по теме '{first_card.topic}' и используй "
                f"минимум два элемента: {', '.join(first_terms)}."
            ),
            expected_format="1 короткое предложение",
            source_topic=first_card.topic,
            placeholder="Коротко сформулируй смысл темы своими словами",
            required_terms=list(first_terms),
            minimum_term_hits=min(_TERMS_PER_TASK, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTaskDTO(
            id="context",
            kind="production",
            title="Контекст",
            prompt=(
                f"Покажи, как тема '{second_card.topic}' проявляется в реальной ситуации. "
                f"Используй минимум два элемента: {', '.join(second_terms)}."
            ),
            expected_format="1-2 короткие строки",
            source_topic=second_card.topic,
            placeholder="Опиши реальную сцену или короткий пример",
            required_terms=list(second_terms),
            minimum_term_hits=min(_TERMS_PER_TASK, len(second_terms)),
            revealed_answer=", ".join(second_terms),
        ),
        PreparedWorkTaskDTO(
            id="meaning",
            kind="production",
            title="Смысл",
            prompt=(
                f"Объясни, почему тема '{third_card.topic}' важна для понимания Японии. "
                f"Используй минимум два элемента: {', '.join(first_terms)}."
            ),
            expected_format="1-2 короткие строки",
            source_topic=third_card.topic,
            placeholder="Объясни смысл темы без длинного эссе",
            required_terms=list(first_terms),
            minimum_term_hits=min(_TERMS_PER_TASK, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTaskDTO(
            id="scene",
            kind="production",
            title="Сцена",
            prompt=_scene_prompt(track, first_terms, first_card.topic),
            expected_format="1-2 короткие строки",
            source_topic=first_card.topic,
            placeholder="Напиши короткий ответ по теме партии",
            required_terms=list(first_terms),
            minimum_term_hits=min(_TERMS_PER_TASK, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTaskDTO(
            id="confidence",
            kind="immersion",
            title="Контроль уверенности",
            prompt=_confidence_prompt(
                track=track,
                current_topic=cards[-1].topic,
                current_terms=current_terms[:_TERMS_PER_TASK],
                review_terms=review_terms[:_REVIEW_TERMS_PER_TASK],
            ),
            expected_format="1-3 строки",
            source_topic=cards[-1].topic,
            placeholder="Свяжи старый и новый материал в одном ответе",
            required_terms=confidence_terms,
            minimum_term_hits=min(_TERMS_PER_TASK, len(confidence_terms)),
            revealed_answer=", ".join(confidence_terms),
        ),
    ]


def _collect_terms(track: TrackType, cards: list[LearningCard]) -> list[str]:
    """Собрать обязательные элементы заданий по карточкам партии.

    Args:
        track: Тип трека обучения.
        cards: Карточки партии.

    Returns:
        Не более шести неповторяющихся элементов.
    """
    if track == TrackType.LANGUAGE:
        return _collect_language_terms(cards)
    return _collect_context_terms(cards)


def _collect_language_terms(cards: list[LearningCard]) -> list[str]:
    """Собрать элементы языковой партии из чтения и перевода примеров.

    Args:
        cards: Карточки партии.

    Returns:
        Список неповторяющихся элементов, при нехватке дополненный темами.
    """
    terms: list[str] = []
    seen: set[str] = set()

    for card in cards:
        for example in card.examples:
            parsed = parse_example(example)
            candidate = _clean_term(parsed["romaji"] or parsed["translation"] or "")
            normalized = normalize_text(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(candidate)
            if len(terms) == _TARGET_TERM_COUNT:
                return terms

    return _extend_with_topics(cards, terms, seen, clean_topic=False)


def _collect_context_terms(cards: list[LearningCard]) -> list[str]:
    """Собрать элементы контекстной партии из терминов и переводов примеров.

    Латинские и числовые последовательности отбрасываются: они попадают в
    ключевые термины как обрывки форматирования и не годятся как обязательный
    элемент ответа.

    Args:
        cards: Карточки партии.

    Returns:
        Список неповторяющихся элементов, при нехватке дополненный темами.
    """
    terms: list[str] = []
    seen: set[str] = set()

    for card in cards:
        for term in card.key_terms:
            cleaned = _clean_term(term)
            if _LATIN_TERM_PATTERN.fullmatch(cleaned.casefold()):
                continue
            normalized = normalize_text(cleaned)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(cleaned)
            if len(terms) == _TARGET_TERM_COUNT:
                return terms

        for example in card.examples:
            parsed = parse_example(example)
            candidate = _clean_term(parsed["translation"] or "")
            normalized = normalize_text(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(candidate)
            if len(terms) == _TARGET_TERM_COUNT:
                return terms

    return _extend_with_topics(cards, terms, seen, clean_topic=True)


def _extend_with_topics(
    cards: list[LearningCard],
    terms: list[str],
    seen: set[str],
    *,
    clean_topic: bool,
) -> list[str]:
    """Дополнить список элементов темами карточек.

    Args:
        cards: Карточки партии.
        terms: Уже собранные элементы.
        seen: Нормализованные значения собранных элементов.
        clean_topic: Очищать ли тему от пунктуации перед подстановкой.

    Returns:
        Дополненный список элементов.
    """
    for card in cards:
        candidate = _clean_term(card.topic) if clean_topic else card.topic
        normalized = normalize_text(candidate)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        terms.append(candidate)
        if len(terms) == _TARGET_TERM_COUNT:
            break
    return terms


def _scene_prompt(track: TrackType, terms: list[str], topic: str) -> str:
    """Сформулировать условие задания на сцену.

    Args:
        track: Тип трека обучения.
        terms: Обязательные элементы ответа.
        topic: Тема карточки-источника.

    Returns:
        Текст условия задания.
    """
    required = ", ".join(terms)
    if track == TrackType.LANGUAGE:
        return (
            f"Сцена: бытовой диалог по теме '{topic}'. Напиши 1-2 строки ответа в ромадзи "
            f"или по-японски и используй минимум два элемента: {required}."
        )
    if track == TrackType.CULTURE:
        return (
            f"Сцена: объясни человеку правило или обычай по теме '{topic}'. "
            f"Используй минимум два элемента: {required}."
        )
    return (
        f"Сцена: коротко объясни событие или перелом по теме '{topic}'. "
        f"Используй минимум два элемента: {required}."
    )


def _confidence_prompt(
    *,
    track: TrackType,
    current_topic: str,
    current_terms: list[str],
    review_terms: list[str],
) -> str:
    """Сформулировать условие на связку старого и нового материала.

    Args:
        track: Тип трека обучения.
        current_topic: Тема последней карточки партии.
        current_terms: Элементы текущей партии.
        review_terms: Элементы предыдущей партии.

    Returns:
        Текст условия задания.
    """
    if track == TrackType.LANGUAGE:
        if review_terms:
            return (
                "Соедини старый и новый материал в одной реплике. Возьми минимум один "
                f"элемент из прошлого: {', '.join(review_terms)} и один из текущей партии: "
                f"{', '.join(current_terms)}. Ответ можно дать в ромадзи. "
                f"Тема текущей партии: '{current_topic}'."
            )
        return (
            f"Сделай короткий ответ по теме '{current_topic}' и используй минимум два "
            f"элемента из текущей партии: {', '.join(current_terms)}. "
            "Ответ можно дать в ромадзи."
        )
    if review_terms:
        return (
            "Соедини старый и новый материал в одной ситуации. Возьми минимум один "
            f"элемент из прошлого: {', '.join(review_terms)} и один из текущей партии: "
            f"{', '.join(current_terms)}. Тема текущей партии: '{current_topic}'."
        )
    return (
        f"Сделай короткий ответ по теме '{current_topic}' и используй минимум два "
        f"элемента из текущей партии: {', '.join(current_terms)}."
    )


def _confidence_terms(current_terms: list[str], review_terms: list[str]) -> list[str]:
    """Объединить элементы предыдущей и текущей партии для задания на связку.

    Args:
        current_terms: Элементы текущей партии.
        review_terms: Элементы предыдущей партии.

    Returns:
        Не более трёх непустых элементов.
    """
    combined = [*review_terms, *current_terms]
    return [term for term in combined if term][:_CONFIDENCE_TERMS_LIMIT]


def _terms_or_topic(
    terms: list[str],
    start: int,
    end: int,
    fallback_topic: str,
) -> list[str]:
    """Взять срез элементов, а при пустом срезе подставить тему карточки.

    Args:
        terms: Полный список элементов партии.
        start: Начало среза.
        end: Конец среза.
        fallback_topic: Тема карточки для подстановки.

    Returns:
        Непустой список элементов либо пустой, если и тема пуста.
    """
    chunk = [term for term in terms[start:end] if term]
    if chunk:
        return chunk
    fallback = _clean_term(fallback_topic)
    return [fallback] if fallback else []


def _clean_term(value: str) -> str:
    """Очистить элемент от перевода и обрамляющей пунктуации.

    Args:
        value: Исходная строка термина или темы.

    Returns:
        Строка, пригодная для подстановки в условие и сверки ответа.
    """
    prepared = key_term_prompt_value(value)
    return str(prepared).strip().strip(_TERM_STRIP_CHARACTERS)
