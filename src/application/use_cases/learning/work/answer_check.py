"""Сверка ответа пользователя с ожидаемым по заданию.

Правила засчёта: точное совпадение после нормализации, допустимые варианты
записи ромадзи, перенос фразы из условия, близость произношения и совпадение
смысла русского перевода. Чтение канны вынесено в kana_reading.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from src.application.dto.learning import PreparedWorkTaskDTO
from src.application.use_cases.learning.work.kana_reading import normalize_pronunciation

_MEANINGLESS_WORDS = frozenset(
    {
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
)

_TRANSLATION_FORMAT_MARKER = "перевод"
_TRANSLATION_TASK_ID = "meaning"
_MIN_MEANING_OVERLAP = 2
_MEANING_OVERLAP_SHARE = 0.6
_MEANING_TOKENS_RATIO = 0.78
_PRONUNCIATION_RATIO = 0.88
_MIN_CONTAINMENT_LENGTH = 4

_WHITESPACE_PATTERN = re.compile(r"\s+")
_PUNCTUATION_PATTERN = re.compile(r"[.,!?;:()\"'`。、「」・]+")
_TOKEN_PATTERN = re.compile(r"[а-яёa-z0-9]+")
_CYRILLIC_PATTERN = re.compile(r"[а-яё]")
_JAPANESE_SCRIPT_PATTERN = re.compile(r"[ぁ-んァ-ヶ一-龯々ー]")
_TRAILED_PHRASE_PATTERN = re.compile(r":\s*(.+?)\s*$")


def answer_matches(task: PreparedWorkTaskDTO, answer: str) -> bool:
    """Проверить, засчитывается ли ответ по правилам задания.

    Открытые задания с обязательными элементами проверяются на их наличие.
    Короткие сверяются со списком допустимых вариантов. Пустой ответ не
    засчитывается ни в одном случае.

    Args:
        task: Подготовленное задание.
        answer: Ответ пользователя.

    Returns:
        True, если ответ верный.
    """
    normalized_answer = normalize_text(answer)
    if not normalized_answer:
        return False

    if task.minimum_term_hits > 0 and task.required_terms:
        hits = 0
        for term in task.required_terms:
            normalized_term = normalize_text(term)
            if normalized_term and normalized_term in normalized_answer:
                hits += 1
        return hits >= task.minimum_term_hits

    return any(
        _answers_are_equivalent(task, answer, expected) for expected in task.expected_answers
    )


def normalize_text(value: str) -> str:
    """Привести текст к сравнению: регистр, пробелы и пунктуация.

    Args:
        value: Исходный текст.

    Returns:
        Текст в нижнем регистре без пунктуации и лишних пробелов.
    """
    compact = _WHITESPACE_PATTERN.sub(" ", value.strip().casefold())
    return _PUNCTUATION_PATTERN.sub("", compact)


def _answers_are_equivalent(task: PreparedWorkTaskDTO, answer: str, expected: str) -> bool:
    """Сравнить ответ с одним ожидаемым вариантом.

    Порядок проверок идёт от точных к более свободным: совпадение после
    нормализации, включение одной строки в другую, перенос японской фразы из
    условия, близость чтения и, только для переводных заданий, совпадение
    смысла по значимым словам.

    Args:
        task: Подготовленное задание.
        answer: Ответ пользователя.
        expected: Очередной ожидаемый вариант.

    Returns:
        True, если ответ совпал с этим вариантом.
    """
    normalized_answer = normalize_text(answer)
    normalized_expected = normalize_text(expected)
    if not normalized_expected:
        return False
    if normalized_answer == normalized_expected:
        return True
    if normalized_expected in normalized_answer or normalized_answer in normalized_expected:
        return True

    prompt_phrase = extract_prompt_phrase(task.prompt)
    if (
        prompt_phrase
        and contains_japanese_script(answer)
        and normalize_text(answer) == normalize_text(prompt_phrase)
    ):
        return True

    answer_pronunciation = normalize_pronunciation(answer)
    expected_pronunciation = normalize_pronunciation(expected)
    if (
        answer_pronunciation
        and expected_pronunciation
        and _is_close_pronunciation(answer_pronunciation, expected_pronunciation)
    ):
        return True

    return _is_task_translation(task) and _is_close_russian_paraphrase(answer, expected)


def _is_close_pronunciation(answer: str, expected: str) -> bool:
    """Совпадает ли чтение с ожидаемым с учётом опечаток.

    Args:
        answer: Приведённое чтение ответа.
        expected: Приведённое чтение ожидаемого ответа.

    Returns:
        True при точном совпадении, вхождении одного чтения в другое длиной
        не меньше четырёх символов либо близости от 0.88.
    """
    if answer == expected:
        return True
    shorter = min(len(answer), len(expected))
    if shorter >= _MIN_CONTAINMENT_LENGTH and (answer in expected or expected in answer):
        return True
    return SequenceMatcher(None, answer, expected).ratio() >= _PRONUNCIATION_RATIO


def _is_task_translation(task: PreparedWorkTaskDTO) -> bool:
    """Является ли задание заданием на перевод на русский.

    Args:
        task: Подготовленное задание.

    Returns:
        True, если формат ответа или идентификатор задания указывают на
        перевод.
    """
    expected_format = task.expected_format.casefold()
    return _TRANSLATION_FORMAT_MARKER in expected_format or task.id == _TRANSLATION_TASK_ID


def _is_close_russian_paraphrase(answer: str, expected: str) -> bool:
    """Передан ли тот же смысл другими русскими словами.

    Сравнение идёт по значимым словам без служебных, поэтому порядок слов и
    мелкие расхождения формулировки на результат не влияют.

    Args:
        answer: Ответ пользователя.
        expected: Ожидаемый ответ.

    Returns:
        True, если оба текста кириллицей и смысл совпадает.
    """
    if not contains_cyrillic(answer) or not contains_cyrillic(expected):
        return False
    answer_tokens = set(meaning_tokens(answer))
    expected_tokens = set(meaning_tokens(expected))
    if not answer_tokens or not expected_tokens:
        return False

    overlap = len(answer_tokens & expected_tokens)
    minimum_overlap = max(_MIN_MEANING_OVERLAP, int(len(expected_tokens) * _MEANING_OVERLAP_SHARE))
    if overlap >= minimum_overlap:
        return True

    normalized_answer = " ".join(sorted(answer_tokens))
    normalized_expected = " ".join(sorted(expected_tokens))
    if not normalized_answer or not normalized_expected:
        return False
    return (
        SequenceMatcher(None, normalized_answer, normalized_expected).ratio()
        >= _MEANING_TOKENS_RATIO
    )


def meaning_tokens(value: str) -> list[str]:
    """Выделить значимые слова текста.

    Args:
        value: Исходный текст.

    Returns:
        Слова длиной от двух символов без служебных, в исходном порядке.
    """
    return [
        token
        for token in _TOKEN_PATTERN.findall(value.casefold())
        if len(token) >= 2 and token not in _MEANINGLESS_WORDS
    ]


def contains_cyrillic(value: str) -> bool:
    """Содержит ли текст кириллические символы.

    Args:
        value: Текст для проверки.

    Returns:
        True при наличии хотя бы одной кириллической буквы.
    """
    return bool(_CYRILLIC_PATTERN.search(value.casefold()))


def contains_japanese_script(value: str) -> bool:
    """Содержит ли текст японскую письменность.

    Args:
        value: Текст для проверки.

    Returns:
        True при наличии кан или иероглифов.
    """
    return bool(_JAPANESE_SCRIPT_PATTERN.search(value))


def extract_prompt_phrase(prompt: str) -> str:
    """Вынести формулировку из конца условия задания.

    Args:
        prompt: Текст условия задания.

    Returns:
        Часть строки после последнего двоеточия либо пустую строку.
    """
    match = _TRAILED_PHRASE_PATTERN.search(prompt)
    return match.group(1).strip() if match else ""
