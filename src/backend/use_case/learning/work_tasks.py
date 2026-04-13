from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re

from src.backend.domain.content import LearningCard, TrackType
from src.backend.dto.learning_dto import (
    TrackWorkResultDTO,
    TrackWorkTaskDTO,
    TrackWorkTaskResultDTO,
    WorkHintDTO,
)
from src.backend.use_case.key_terms import key_term_prompt_value


@dataclass(slots=True)
class PreparedWorkTask:
    id: str
    kind: str
    title: str
    prompt: str
    expected_format: str
    source_topic: str
    placeholder: str
    required_terms: list[str] = field(default_factory=list)
    hints: list[WorkHintDTO] = field(default_factory=list)
    expected_answers: list[str] = field(default_factory=list)
    minimum_term_hits: int = 0
    revealed_answer: str | None = None


def build_prepared_work_tasks(
    track: TrackType,
    cards: list[LearningCard],
    review_cards: list[LearningCard] | None = None,
) -> list[PreparedWorkTask]:
    if not cards:
        return []

    current_terms = _collect_terms_for_work(track, cards)
    review_terms = _collect_terms_for_work(track, review_cards or [])

    if track == TrackType.LANGUAGE:
        parsed_examples = _select_work_examples(cards)
        if not parsed_examples:
            parsed_examples.append(
                (
                    cards[0],
                    {
                        "japanese": cards[0].topic,
                        "romaji": "",
                        "translation": cards[0].topic,
                    },
                )
            )
        while len(parsed_examples) < 3:
            parsed_examples.append(parsed_examples[-1])
        return _build_language_work_tasks(
            cards=cards,
            parsed_examples=parsed_examples,
            current_terms=current_terms,
            review_terms=review_terms,
        )

    return _build_context_work_tasks(
        track=track,
        cards=cards,
        current_terms=current_terms,
        review_terms=review_terms,
    )


def to_track_work_task_dto(
    task: PreparedWorkTask,
    submitted_answer: str | None = None,
) -> TrackWorkTaskDTO:
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
    task: PreparedWorkTask,
    submitted_answer: str | None = None,
) -> dict[str, object]:
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


def evaluate_work_submission(
    tasks: list[PreparedWorkTask],
    answers: dict[str, str],
    *,
    track: TrackType,
) -> TrackWorkResultDTO:
    task_results: list[TrackWorkTaskResultDTO] = []
    correct = 0

    for task in tasks:
        answer = str(answers.get(task.id) or "").strip()
        is_correct = _answer_matches(task, answer)
        if is_correct:
            correct += 1
        task_results.append(
            TrackWorkTaskResultDTO(
                task_id=task.id,
                is_correct=is_correct,
                feedback=_build_feedback(task, is_correct),
                revealed_answer=None if is_correct else task.revealed_answer,
            )
        )

    score = round((correct / len(tasks)) * 100) if tasks else 0
    pass_score = 80
    passed = score >= pass_score
    summary = (
        "Материал по этой партии держится уверенно."
        if passed
        else "По партии еще есть пробелы. Лучше еще раз пройти карточки и повторить работу."
    )
    verdict = (
        "Система видит, что этот набор уже можно использовать в коротких ответах и сценах."
        if passed
        else "Система пока не уверена, что этот набор закрепился в практике."
    )
    certificate_statement = None
    if passed and track == TrackType.LANGUAGE and score >= 100:
        certificate_statement = (
            "По этой партии система считает, что бытовые конструкции используются без заметной опоры на подсказки."
        )
    return TrackWorkResultDTO(
        score=score,
        pass_score=pass_score,
        passed=passed,
        summary=summary,
        verdict=verdict,
        certificate_statement=certificate_statement,
        task_results=task_results,
    )


def _answer_matches(task: PreparedWorkTask, answer: str) -> bool:
    normalized_answer = _normalize_text(answer)
    if not normalized_answer:
        return False
    if task.minimum_term_hits > 0 and task.required_terms:
        hits = 0
        for term in task.required_terms:
            normalized_term = _normalize_text(term)
            if normalized_term and normalized_term in normalized_answer:
                hits += 1
        return hits >= task.minimum_term_hits
    for expected in task.expected_answers:
        if _answers_are_equivalent(task, answer, expected):
            return True
    return False


def _answers_are_equivalent(
    task: PreparedWorkTask,
    answer: str,
    expected: str,
) -> bool:
    normalized_answer = _normalize_text(answer)
    normalized_expected = _normalize_text(expected)
    if not normalized_expected:
        return False
    if normalized_answer == normalized_expected:
        return True
    if normalized_expected in normalized_answer or normalized_answer in normalized_expected:
        return True
    prompt_phrase = _extract_prompt_phrase(task.prompt)
    if (
        prompt_phrase
        and _contains_japanese_script(answer)
        and _normalize_text(answer) == _normalize_text(prompt_phrase)
    ):
        return True

    normalized_answer_pronunciation = _normalize_pronunciation(answer)
    normalized_expected_pronunciation = _normalize_pronunciation(expected)
    if (
        normalized_answer_pronunciation
        and normalized_expected_pronunciation
        and _is_close_pronunciation(
            normalized_answer_pronunciation,
            normalized_expected_pronunciation,
        )
    ):
        return True

    if _is_translation_task(task) and _is_close_russian_paraphrase(answer, expected):
        return True

    return False


def _build_feedback(task: PreparedWorkTask, is_correct: bool) -> str:
    if is_correct:
        if task.kind in {"production", "immersion"}:
            return "Задание закрыто: нужный материал использован в ответе."
        return "Ответ совпадает с материалом партии."
    if task.kind in {"production", "immersion"}:
        return "В ответе не хватает нужных элементов из пройденного материала."
    return "Ответ не совпал с тем, что было в карточках этой партии."


def _parse_example(example: str) -> dict[str, str]:
    parts = [part.strip() for part in example.split("|")]
    if len(parts) >= 3:
        japanese, romaji, translation = parts[:3]
        return {
            "japanese": japanese,
            "romaji": romaji,
            "translation": translation,
        }
    if len(parts) == 2:
        japanese, translation = parts
        return {"japanese": japanese, "romaji": "", "translation": translation}
    return {"japanese": example.strip(), "romaji": "", "translation": ""}


def _select_work_examples(
    cards: list[LearningCard],
) -> list[tuple[LearningCard, dict[str, str]]]:
    selected: list[tuple[LearningCard, dict[str, str]]] = []

    for card in cards:
        first_valid = None
        for example in card.examples:
            parsed = _parse_example(example)
            if parsed["japanese"]:
                first_valid = parsed
                break
        if first_valid is not None:
            selected.append((card, first_valid))

    if len(selected) >= 3:
        return selected

    for card in cards:
        for example in card.examples:
            parsed = _parse_example(example)
            if not parsed["japanese"]:
                continue
            if any(
                existing_card.id == card.id
                and existing_example["japanese"] == parsed["japanese"]
                for existing_card, existing_example in selected
            ):
                continue
            selected.append((card, parsed))
            if len(selected) >= 3:
                return selected

    return selected


def _build_language_work_tasks(
    *,
    cards: list[LearningCard],
    parsed_examples: list[tuple[LearningCard, dict[str, str]]],
    current_terms: list[str],
    review_terms: list[str],
) -> list[PreparedWorkTask]:
    first_card, first_example = parsed_examples[0]
    second_card, second_example = parsed_examples[1]
    third_card, third_example = parsed_examples[2]
    confidence_terms = _confidence_terms(current_terms[:2], review_terms[:1])

    return [
        PreparedWorkTask(
            id="reading",
            kind="recall",
            title="Чтение",
            prompt=f"Запиши ромадзи для фразы: {first_example['japanese']}",
            expected_format="ромадзи",
            source_topic=first_card.topic,
            placeholder="Например: watashi wa ...",
            expected_answers=[first_example["romaji"]],
            revealed_answer=first_example["romaji"],
        ),
        PreparedWorkTask(
            id="meaning",
            kind="recall",
            title="Перевод",
            prompt=f"Переведи на русский: {second_example['japanese']}",
            expected_format="краткий перевод",
            source_topic=second_card.topic,
            placeholder="Например: я иду в школу",
            expected_answers=[second_example["translation"]],
            revealed_answer=second_example["translation"],
        ),
        PreparedWorkTask(
            id="recall",
            kind="recall",
            title="Фраза по памяти",
            prompt=f"Восстанови фразу по памяти: {third_example['translation'] or third_card.topic}",
            expected_format="ромадзи или японский",
            source_topic=third_card.topic,
            placeholder="Можно в ромадзи, японская раскладка не обязательна",
            expected_answers=[
                answer
                for answer in (third_example["japanese"], third_example["romaji"])
                if answer
            ],
            revealed_answer=third_example["romaji"] or third_example["japanese"],
        ),
        PreparedWorkTask(
            id="scene",
            kind="production",
            title="Сцена",
            prompt=_scene_prompt(track=TrackType.LANGUAGE, terms=current_terms[:2], topic=cards[0].topic),
            expected_format="1-2 строки, можно в ромадзи",
            source_topic=cards[0].topic,
            placeholder="Напиши короткий ответ. Можно в ромадзи.",
            required_terms=current_terms[:2],
            minimum_term_hits=min(2, len(current_terms[:2])),
            revealed_answer=", ".join(current_terms[:2]),
        ),
        PreparedWorkTask(
            id="confidence",
            kind="immersion",
            title="Контроль уверенности",
            prompt=_confidence_prompt(
                track=TrackType.LANGUAGE,
                current_topic=cards[-1].topic,
                current_terms=current_terms[:2],
                review_terms=review_terms[:1],
            ),
            expected_format="1-3 строки, можно в ромадзи",
            source_topic=cards[-1].topic,
            placeholder="Соедини старый и новый материал. Можно в ромадзи.",
            required_terms=confidence_terms,
            minimum_term_hits=min(2, len(confidence_terms)),
            revealed_answer=", ".join(confidence_terms),
        ),
    ]


def _build_context_work_tasks(
    *,
    track: TrackType,
    cards: list[LearningCard],
    current_terms: list[str],
    review_terms: list[str],
) -> list[PreparedWorkTask]:
    first_card = cards[0]
    second_card = cards[1] if len(cards) > 1 else cards[0]
    third_card = cards[2] if len(cards) > 2 else cards[-1]
    first_terms = _slice_terms_or_topic(current_terms, 0, 2, first_card.topic)
    second_terms = _slice_terms_or_topic(current_terms, 2, 4, second_card.topic)
    confidence_terms = _confidence_terms(current_terms[:2], review_terms[:1])
    if not confidence_terms:
        confidence_terms = _slice_terms_or_topic(current_terms, 0, 2, cards[-1].topic)

    return [
        PreparedWorkTask(
            id="thesis",
            kind="production",
            title="Тезис",
            prompt=f"Собери 1 короткое предложение по теме '{first_card.topic}' и используй минимум два элемента: {', '.join(first_terms)}.",
            expected_format="1 короткое предложение",
            source_topic=first_card.topic,
            placeholder="Коротко сформулируй смысл темы своими словами",
            required_terms=first_terms,
            minimum_term_hits=min(2, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTask(
            id="context",
            kind="production",
            title="Контекст",
            prompt=f"Покажи, как тема '{second_card.topic}' проявляется в реальной ситуации. Используй минимум два элемента: {', '.join(second_terms)}.",
            expected_format="1-2 короткие строки",
            source_topic=second_card.topic,
            placeholder="Опиши реальную сцену или короткий пример",
            required_terms=second_terms,
            minimum_term_hits=min(2, len(second_terms)),
            revealed_answer=", ".join(second_terms),
        ),
        PreparedWorkTask(
            id="meaning",
            kind="production",
            title="Смысл",
            prompt=f"Объясни, почему тема '{third_card.topic}' важна для понимания Японии. Используй минимум два элемента: {', '.join(first_terms)}.",
            expected_format="1-2 короткие строки",
            source_topic=third_card.topic,
            placeholder="Объясни смысл темы без длинного эссе",
            required_terms=first_terms,
            minimum_term_hits=min(2, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTask(
            id="scene",
            kind="production",
            title="Сцена",
            prompt=_scene_prompt(track, first_terms, first_card.topic),
            expected_format="1-2 короткие строки",
            source_topic=first_card.topic,
            placeholder="Напиши короткий ответ по теме партии",
            required_terms=first_terms,
            minimum_term_hits=min(2, len(first_terms)),
            revealed_answer=", ".join(first_terms),
        ),
        PreparedWorkTask(
            id="confidence",
            kind="immersion",
            title="Контроль уверенности",
            prompt=_confidence_prompt(
                track=track,
                current_topic=cards[-1].topic,
                current_terms=current_terms[:2],
                review_terms=review_terms[:1],
            ),
            expected_format="1-3 строки",
            source_topic=cards[-1].topic,
            placeholder="Свяжи старый и новый материал в одном ответе",
            required_terms=confidence_terms,
            minimum_term_hits=min(2, len(confidence_terms)),
            revealed_answer=", ".join(confidence_terms),
        ),
    ]


def _collect_terms_for_work(track: TrackType, cards: list[LearningCard]) -> list[str]:
    if track == TrackType.LANGUAGE:
        return _collect_language_terms(cards)
    return _collect_context_terms(cards)


def _collect_language_terms(cards: list[LearningCard]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for card in cards:
        for example in card.examples:
            parsed = _parse_example(example)
            candidate = _clean_work_term(parsed["romaji"] or parsed["translation"])
            normalized = _normalize_text(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(candidate)
            if len(terms) == 6:
                return terms
    for card in cards:
        normalized = _normalize_text(card.topic)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        terms.append(card.topic)
        if len(terms) == 6:
            return terms
    return terms


def _collect_context_terms(cards: list[LearningCard]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for card in cards:
        for term in card.key_terms:
            cleaned_term = _clean_work_term(term)
            if re.fullmatch(r"[a-z0-9 _/-]+", cleaned_term.casefold()):
                continue
            normalized = _normalize_text(cleaned_term)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(cleaned_term)
            if len(terms) == 6:
                return terms
        for example in card.examples:
            parsed = _parse_example(example)
            candidate = _clean_work_term(parsed["translation"])
            normalized = _normalize_text(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(candidate)
            if len(terms) == 6:
                return terms
    for card in cards:
        cleaned_topic = _clean_work_term(card.topic)
        normalized = _normalize_text(cleaned_topic)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        terms.append(cleaned_topic)
        if len(terms) == 6:
            return terms
    return terms


def _scene_prompt(track: TrackType, terms: list[str], topic: str) -> str:
    if track == TrackType.LANGUAGE:
        return (
            f"Сцена: бытовой диалог по теме '{topic}'. Напиши 1-2 строки ответа в ромадзи или по-японски и используй "
            f"минимум два элемента: {', '.join(terms)}."
        )
    if track == TrackType.CULTURE:
        return (
            f"Сцена: объясни человеку правило или обычай по теме '{topic}'. Используй минимум два элемента: "
            f"{', '.join(terms)}."
        )
    return (
        f"Сцена: коротко объясни событие или перелом по теме '{topic}'. Используй минимум два элемента: "
        f"{', '.join(terms)}."
    )


def _confidence_prompt(
    *,
    track: TrackType,
    current_topic: str,
    current_terms: list[str],
    review_terms: list[str],
) -> str:
    if track == TrackType.LANGUAGE:
        if review_terms:
            return (
                f"Соедини старый и новый материал в одной реплике. Возьми минимум один элемент из прошлого: "
                f"{', '.join(review_terms)} и один из текущей партии: {', '.join(current_terms)}. "
                f"Ответ можно дать в ромадзи. Тема текущей партии: '{current_topic}'."
            )
        return (
            f"Сделай короткий ответ по теме '{current_topic}' и используй минимум два элемента из текущей партии: "
            f"{', '.join(current_terms)}. Ответ можно дать в ромадзи."
        )
    if review_terms:
        return (
            f"Соедини старый и новый материал в одной ситуации. Возьми минимум один элемент из прошлого: "
            f"{', '.join(review_terms)} и один из текущей партии: {', '.join(current_terms)}. "
            f"Тема текущей партии: '{current_topic}'."
        )
    return (
        f"Сделай короткий ответ по теме '{current_topic}' и используй минимум два элемента из текущей партии: "
        f"{', '.join(current_terms)}."
    )


def _confidence_terms(current_terms: list[str], review_terms: list[str]) -> list[str]:
    terms = [*review_terms, *current_terms]
    return [term for term in terms if term][:3]


def _normalize_text(value: str) -> str:
    compact = re.sub(r"\s+", " ", value.strip().casefold())
    compact = re.sub(r"[.,!?;:()\"'`。、「」・]+", "", compact)
    return compact


def _normalize_pronunciation(value: str) -> str:
    prepared = _kana_to_romaji(value)
    compact = re.sub(r"[^a-z0-9]", "", prepared.casefold())
    if not compact:
        return ""
    compact = compact.replace("shi", "si")
    compact = compact.replace("chi", "ti")
    compact = compact.replace("tsu", "tu")
    compact = compact.replace("fu", "hu")
    compact = re.sub(r"nn(?=[aiueoy])", "n", compact)
    compact = re.sub(r"ou", "o", compact)
    compact = re.sub(r"oo", "o", compact)
    compact = re.sub(r"uu", "u", compact)
    return compact


def _is_close_pronunciation(answer: str, expected: str) -> bool:
    if answer == expected:
        return True
    shorter = min(len(answer), len(expected))
    if shorter >= 4 and (answer in expected or expected in answer):
        return True
    return SequenceMatcher(None, answer, expected).ratio() >= 0.88


def _is_translation_task(task: PreparedWorkTask) -> bool:
    expected_format = task.expected_format.casefold()
    return "перевод" in expected_format or task.id == "meaning"


def _is_close_russian_paraphrase(answer: str, expected: str) -> bool:
    if not _contains_cyrillic(answer) or not _contains_cyrillic(expected):
        return False
    answer_tokens = set(_meaning_tokens(answer))
    expected_tokens = set(_meaning_tokens(expected))
    if not answer_tokens or not expected_tokens:
        return False
    overlap = len(answer_tokens & expected_tokens)
    minimum_overlap = max(2, int(len(expected_tokens) * 0.6))
    if overlap >= minimum_overlap:
        return True
    normalized_answer = " ".join(sorted(answer_tokens))
    normalized_expected = " ".join(sorted(expected_tokens))
    if not normalized_answer or not normalized_expected:
        return False
    return SequenceMatcher(None, normalized_answer, normalized_expected).ratio() >= 0.78


def _meaning_tokens(value: str) -> list[str]:
    stop_words = {
        "а",
        "без",
        "был",
        "быть",
        "в",
        "во",
        "вот",
        "вы",
        "да",
        "для",
        "до",
        "его",
        "ее",
        "если",
        "есть",
        "же",
        "за",
        "здесь",
        "и",
        "из",
        "или",
        "их",
        "к",
        "как",
        "ли",
        "мне",
        "можно",
        "мой",
        "мы",
        "на",
        "не",
        "нее",
        "но",
        "ну",
        "он",
        "она",
        "они",
        "от",
        "по",
        "под",
        "пожалуйста",
        "прошу",
        "с",
        "со",
        "так",
        "там",
        "то",
        "тут",
        "ты",
        "у",
        "уже",
        "что",
        "это",
        "я",
    }
    return [
        token
        for token in re.findall(r"[а-яёa-z0-9]+", value.casefold())
        if len(token) >= 2 and token not in stop_words
    ]


def _contains_cyrillic(value: str) -> bool:
    return bool(re.search(r"[а-яё]", value.casefold()))


def _contains_japanese_script(value: str) -> bool:
    return bool(re.search(r"[ぁ-んァ-ヶ一-龯々ー]", value))


def _extract_prompt_phrase(prompt: str) -> str:
    match = re.search(r":\s*(.+?)\s*$", prompt)
    if not match:
        return ""
    return match.group(1).strip()


def _kana_to_romaji(value: str) -> str:
    digraph_map = {
        "きゃ": "kya",
        "きゅ": "kyu",
        "きょ": "kyo",
        "しゃ": "sha",
        "しゅ": "shu",
        "しょ": "sho",
        "ちゃ": "cha",
        "ちゅ": "chu",
        "ちょ": "cho",
        "にゃ": "nya",
        "にゅ": "nyu",
        "にょ": "nyo",
        "ひゃ": "hya",
        "ひゅ": "hyu",
        "ひょ": "hyo",
        "みゃ": "mya",
        "みゅ": "myu",
        "みょ": "myo",
        "りゃ": "rya",
        "りゅ": "ryu",
        "りょ": "ryo",
        "ぎゃ": "gya",
        "ぎゅ": "gyu",
        "ぎょ": "gyo",
        "じゃ": "ja",
        "じゅ": "ju",
        "じょ": "jo",
        "びゃ": "bya",
        "びゅ": "byu",
        "びょ": "byo",
        "ぴゃ": "pya",
        "ぴゅ": "pyu",
        "ぴょ": "pyo",
        "キャ": "kya",
        "キュ": "kyu",
        "キョ": "kyo",
        "シャ": "sha",
        "シュ": "shu",
        "ショ": "sho",
        "チャ": "cha",
        "チュ": "chu",
        "チョ": "cho",
        "ニャ": "nya",
        "ニュ": "nyu",
        "ニョ": "nyo",
        "ヒャ": "hya",
        "ヒュ": "hyu",
        "ヒョ": "hyo",
        "ミャ": "mya",
        "ミュ": "myu",
        "ミョ": "myo",
        "リャ": "rya",
        "リュ": "ryu",
        "リョ": "ryo",
        "ギャ": "gya",
        "ギュ": "gyu",
        "ギョ": "gyo",
        "ジャ": "ja",
        "ジュ": "ju",
        "ジョ": "jo",
        "ビャ": "bya",
        "ビュ": "byu",
        "ビョ": "byo",
        "ピャ": "pya",
        "ピュ": "pyu",
        "ピョ": "pyo",
    }
    char_map = {
        "あ": "a",
        "い": "i",
        "う": "u",
        "え": "e",
        "お": "o",
        "か": "ka",
        "き": "ki",
        "く": "ku",
        "け": "ke",
        "こ": "ko",
        "さ": "sa",
        "し": "shi",
        "す": "su",
        "せ": "se",
        "そ": "so",
        "た": "ta",
        "ち": "chi",
        "つ": "tsu",
        "て": "te",
        "と": "to",
        "な": "na",
        "に": "ni",
        "ぬ": "nu",
        "ね": "ne",
        "の": "no",
        "は": "ha",
        "ひ": "hi",
        "ふ": "fu",
        "へ": "he",
        "ほ": "ho",
        "ま": "ma",
        "み": "mi",
        "む": "mu",
        "め": "me",
        "も": "mo",
        "や": "ya",
        "ゆ": "yu",
        "よ": "yo",
        "ら": "ra",
        "り": "ri",
        "る": "ru",
        "れ": "re",
        "ろ": "ro",
        "わ": "wa",
        "を": "o",
        "ん": "n",
        "が": "ga",
        "ぎ": "gi",
        "ぐ": "gu",
        "げ": "ge",
        "ご": "go",
        "ざ": "za",
        "じ": "ji",
        "ず": "zu",
        "ぜ": "ze",
        "ぞ": "zo",
        "だ": "da",
        "ぢ": "ji",
        "づ": "zu",
        "で": "de",
        "ど": "do",
        "ば": "ba",
        "び": "bi",
        "ぶ": "bu",
        "べ": "be",
        "ぼ": "bo",
        "ぱ": "pa",
        "ぴ": "pi",
        "ぷ": "pu",
        "ぺ": "pe",
        "ぽ": "po",
        "ぁ": "a",
        "ぃ": "i",
        "ぅ": "u",
        "ぇ": "e",
        "ぉ": "o",
        "ア": "a",
        "イ": "i",
        "ウ": "u",
        "エ": "e",
        "オ": "o",
        "カ": "ka",
        "キ": "ki",
        "ク": "ku",
        "ケ": "ke",
        "コ": "ko",
        "サ": "sa",
        "シ": "shi",
        "ス": "su",
        "セ": "se",
        "ソ": "so",
        "タ": "ta",
        "チ": "chi",
        "ツ": "tsu",
        "テ": "te",
        "ト": "to",
        "ナ": "na",
        "ニ": "ni",
        "ヌ": "nu",
        "ネ": "ne",
        "ノ": "no",
        "ハ": "ha",
        "ヒ": "hi",
        "フ": "fu",
        "ヘ": "he",
        "ホ": "ho",
        "マ": "ma",
        "ミ": "mi",
        "ム": "mu",
        "メ": "me",
        "モ": "mo",
        "ヤ": "ya",
        "ユ": "yu",
        "ヨ": "yo",
        "ラ": "ra",
        "リ": "ri",
        "ル": "ru",
        "レ": "re",
        "ロ": "ro",
        "ワ": "wa",
        "ヲ": "o",
        "ン": "n",
        "ガ": "ga",
        "ギ": "gi",
        "グ": "gu",
        "ゲ": "ge",
        "ゴ": "go",
        "ザ": "za",
        "ジ": "ji",
        "ズ": "zu",
        "ゼ": "ze",
        "ゾ": "zo",
        "ダ": "da",
        "ヂ": "ji",
        "ヅ": "zu",
        "デ": "de",
        "ド": "do",
        "バ": "ba",
        "ビ": "bi",
        "ブ": "bu",
        "ベ": "be",
        "ボ": "bo",
        "パ": "pa",
        "ピ": "pi",
        "プ": "pu",
        "ペ": "pe",
        "ポ": "po",
        "ァ": "a",
        "ィ": "i",
        "ゥ": "u",
        "ェ": "e",
        "ォ": "o",
    }

    chunks: list[str] = []
    index = 0
    while index < len(value):
        pair = value[index : index + 2]
        if pair in digraph_map:
            chunks.append(digraph_map[pair])
            index += 2
            continue

        char = value[index]
        if char in {"っ", "ッ"}:
            next_pair = value[index + 1 : index + 3]
            next_chunk = digraph_map.get(next_pair)
            if next_chunk:
                chunks.append(next_chunk[:1])
            elif index + 1 < len(value):
                next_char = char_map.get(value[index + 1], "")
                if next_char:
                    chunks.append(next_char[:1])
            index += 1
            continue
        if char == "ー":
            if chunks and chunks[-1]:
                last_vowel_match = re.search(r"[aeiou](?!.*[aeiou])", chunks[-1])
                if last_vowel_match:
                    chunks.append(last_vowel_match.group(0))
            index += 1
            continue

        mapped = char_map.get(char)
        if mapped is not None:
            chunks.append(mapped)
        else:
            chunks.append(char)
        index += 1

    return "".join(chunks)


def _clean_work_term(value: str) -> str:
    prepared = key_term_prompt_value(value)
    return str(prepared).strip().strip(".,!;:()[]{}\"'`")


def _slice_terms_or_topic(
    terms: list[str],
    start: int,
    end: int,
    fallback_topic: str,
) -> list[str]:
    chunk = [term for term in terms[start:end] if term]
    if chunk:
        return chunk
    fallback = _clean_work_term(fallback_topic)
    return [fallback] if fallback else []
