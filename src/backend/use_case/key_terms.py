from __future__ import annotations

import re

from src.backend.dto.learning_dto import KeyTermDTO

_TERM_TRANSLATIONS = {
    "挨拶": "приветствие",
    "丁寧": "вежливая форма",
    "会話": "разговор",
    "自己紹介": "самопрезентация",
    "名前": "имя",
    "よろしく": "вежливая завершающая формула",
    "注文": "заказ",
    "お願い": "просьба",
    "おすすめ": "рекомендация",
    "会計": "счет",
    "メニュー": "меню",
    "水": "вода",
    "電車": "поезд",
    "駅": "станция",
    "移動": "перемещение",
    "質問": "вопрос",
    "買い物": "покупки",
    "店": "магазин",
    "試着": "примерка",
    "現金": "наличные",
    "大学": "университет",
    "勉強": "учеба",
    "確認": "уточнение",
    "仕事": "работа",
    "共有": "обмен информацией",
    "住まい": "жилье",
    "契約": "договор",
    "生活": "быт",
    "助詞": "частица",
    "主題": "тема",
    "主語": "подлежащее",
    "対象": "объект действия",
    "方向": "направление",
    "所有": "принадлежность",
    "否定": "отрицание",
    "過去": "прошедшее время",
    "動詞": "глагол",
    "文": "предложение",
    "語彙": "лексика",
    "路線図": "схема линий",
    "乗り場": "платформа",
    "乗り換え": "пересадка",
    "資料": "материалы",
    "課題": "задание",
    "進捗": "прогресс задачи",
    "教室": "аудитория",
    "会議": "встреча",
    "不動産屋": "агентство жилья",
    "地図": "карта",
    "言い方": "формулировка",
    "表現": "выражение",
    "歴史": "история",
    "文化": "культура",
    "時代": "эпоха",
    "変化": "изменение",
    "伝統": "традиция",
    "習慣": "привычка",
    "礼儀": "этикет",
    "空気": "атмосфера общения",
    "city": "город",
    "memory": "память",
    "place": "место",
    "language": "язык",
    "history": "история",
    "culture": "культура",
    "work": "работа",
}


def build_key_term_dtos(raw_terms: list[str]) -> list[KeyTermDTO]:
    items: list[KeyTermDTO] = []
    seen: set[str] = set()
    for raw_term in raw_terms:
        label, translation = parse_key_term(raw_term)
        if not label:
            continue
        normalized = _normalize_term_key(label, translation)
        if normalized in seen:
            continue
        seen.add(normalized)
        items.append(
            KeyTermDTO(
                raw_text=str(raw_term).strip(),
                label=label,
                translation=translation,
            )
        )
    return items


def parse_key_term(raw_term: str) -> tuple[str, str | None]:
    cleaned = " ".join(str(raw_term or "").split()).strip(" ,.;")
    if not cleaned:
        return "", None

    bracket_match = re.fullmatch(r"(.+?)\s*\((.+?)\)", cleaned)
    if bracket_match:
        label = bracket_match.group(1).strip()
        translation = bracket_match.group(2).strip()
        return label, translation or None

    for separator in ("|", " - ", " — ", " – ", ":", " -> "):
        if separator not in cleaned:
            continue
        parts = [part.strip(" ,.;") for part in cleaned.split(separator) if part.strip(" ,.;")]
        if len(parts) >= 2:
            label = parts[0]
            translation = parts[-1]
            if translation == label:
                translation = None
            return label, translation

    translation = _TERM_TRANSLATIONS.get(cleaned)
    if translation is None:
        translation = _TERM_TRANSLATIONS.get(cleaned.casefold())
    if translation == cleaned:
        translation = None
    return cleaned, translation


def key_term_prompt_value(raw_term: str) -> str:
    label, translation = parse_key_term(raw_term)
    return translation or label


def key_term_input_value(raw_term: str) -> str:
    label, translation = parse_key_term(raw_term)
    if label and translation:
        return f"{label} - {translation}"
    return label


def _normalize_term_key(label: str, translation: str | None) -> str:
    combined = f"{label}|{translation or ''}"
    compact = re.sub(r"\s+", " ", combined.strip().casefold())
    return compact.replace("ё", "е")
