"""Чтение канны и приведение произношения к единой записи.

Таблицы соответствия слогов и правила сведения вариантов ромадзи нужны
сверке ответов, поэтому лежат рядом с ней и ни от каких слоёв не зависят.
"""

from __future__ import annotations

import re

_HIRAGANA_DIGRAPHS = {
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
}

_KATAKANA_DIGRAPHS = {
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

_HIRAGANA_SYLLABLES = {
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
}

_KATAKANA_SYLLABLES = {
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

_DIGRAPHS = {**_HIRAGANA_DIGRAPHS, **_KATAKANA_DIGRAPHS}
_SYLLABLES = {**_HIRAGANA_SYLLABLES, **_KATAKANA_SYLLABLES}
_GEMINATION_MARKS = frozenset({"っ", "ッ"})
_LONG_VOWEL_MARK = "ー"
_LAST_VOWEL_PATTERN = re.compile(r"[aeiou](?!.*[aeiou])")
_NON_LATIN_PATTERN = re.compile(r"[^a-z0-9]")
_N_BEFORE_VOWEL_PATTERN = re.compile(r"nn(?=[aiueoy])")
_LONG_O_PATTERN = re.compile(r"ou")
_LONG_OO_PATTERN = re.compile(r"oo")
_LONG_UU_PATTERN = re.compile(r"uu")


def to_romaji(value: str) -> str:
    """Преобразовать канный текст в латинское чтение.

    Символы, не входящие в таблицы, переносятся без изменений, поэтому
    функция безопасна для смешанных строк: ромадзи в неё можно передавать
    как есть.

    Args:
        value: Исходный текст: каны, ромадзи или их смесь.

    Returns:
        Текст, где хирагана и катакана записаны ромадзи.
    """
    chunks: list[str] = []
    index = 0
    while index < len(value):
        digraph = value[index : index + 2]
        if digraph in _DIGRAPHS:
            chunks.append(_DIGRAPHS[digraph])
            index += 2
            continue

        char = value[index]
        if char in _GEMINATION_MARKS:
            chunks.append(_gemination_chunk(value, index))
            index += 1
            continue

        if char == _LONG_VOWEL_MARK:
            chunks.append(_long_vowel_chunk(chunks))
            index += 1
            continue

        chunks.append(_SYLLABLES.get(char, char))
        index += 1

    return "".join(chunks)


def normalize_pronunciation(value: str) -> str:
    """Привести чтение японского текста к единой латинской записи.

    После перевода канны в чтение сводятся распространённые варианты записи
    одного звука: shi и si, chi и ti, tsu и tu, fu и hu, а также долгота
    гласных и написание ん перед гласной.

    Args:
        value: Исходный текст: каны, ромадзи или их смесь.

    Returns:
        Строка только из строчных латинских букв и цифр; пустая, если
        читаемых слогов в тексте нет.
    """
    prepared = to_romaji(value)
    compact = _NON_LATIN_PATTERN.sub("", prepared.casefold())
    if not compact:
        return ""
    compact = compact.replace("shi", "si")
    compact = compact.replace("chi", "ti")
    compact = compact.replace("tsu", "tu")
    compact = compact.replace("fu", "hu")
    compact = _N_BEFORE_VOWEL_PATTERN.sub("n", compact)
    compact = _LONG_O_PATTERN.sub("o", compact)
    compact = _LONG_OO_PATTERN.sub("o", compact)
    compact = _LONG_UU_PATTERN.sub("u", compact)
    return compact


def _gemination_chunk(value: str, index: int) -> str:
    """Вернуть согласную, удваиваемую слогом после маленького つ.

    Args:
        value: Исходный текст.
        index: Позиция знака удвоения.

    Returns:
        Первая буква чтения следующего слога либо пустая строка.
    """
    following = _DIGRAPHS.get(value[index + 1 : index + 3])
    if not following and index + 1 < len(value):
        following = _SYLLABLES.get(value[index + 1], "")
    return following[:1]


def _long_vowel_chunk(chunks: list[str]) -> str:
    """Вернуть гласную для prolongation-черты по последнему слогу.

    Args:
        chunks: Уже собранные части чтения.

    Returns:
        Последняя гласная предыдущего слога либо пустая строка.
    """
    if not chunks or not chunks[-1]:
        return ""
    match = _LAST_VOWEL_PATTERN.search(chunks[-1])
    return match.group(0) if match else ""
