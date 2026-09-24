"""Заготовочный учебный контент как данные, а не как код.

Раньше готовые темы, переводы и примеры лежали литералом внутри инфраструктурного
модуля LLM-клиента: правка формулировки требовала изменения кода и ревью Python,
а само содержание не имело отношения к тому, как ходить в API провайдера. Теперь
текст живёт в JSON рядом с этим модулем, а здесь остаётся только чтение и проверка.

Проверка обязательна: заготовки — тот самый путь, который работает, когда модель
недоступна. Молча пустой файл означал бы, что запасной контент исчезает именно
тогда, когда он нужен, и узнаёшь об этом уже в аварии.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent / "fallback_data"
CARDS_FILE = "cards.json"
SCENES_FILE = "language_scenes.json"
REQUIRED_TRACKS = ("language", "culture", "history")
SCENE_FIELDS = (
    "request_jp",
    "request_ro",
    "request_ru",
    "option_jp",
    "option_ro",
    "option_ru",
    "action_jp",
    "action_ro",
    "action_ru",
    "place_jp",
    "place_ro",
    "place_ru",
)


class FallbackContentError(RuntimeError):
    """Файл заготовочного контента отсутствует, испорчен или неполон."""


@dataclass(frozen=True, slots=True)
class FallbackCard:
    """Одна заготовочная карточка.

    Атрибуты:
        topic: Тема карточки.
        explanation: Объяснение темы.
        examples: Примеры употребления.
        key_terms: Ключевые термины.
    """

    topic: str
    explanation: str
    examples: list[str]
    key_terms: list[str]


def _read_json(name: str) -> object:
    """Прочитать и разобрать файл контента.

    Args:
        name: Имя файла в каталоге контента.

    Returns:
        Разобранные данные.

    Raises:
        FallbackContentError: Если файла нет или он не разбирается.
    """
    path = CONTENT_DIR / name
    if not path.is_file():
        raise FallbackContentError(f"Файл заготовочного контента не найден: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FallbackContentError(f"Файл {path} не является корректным JSON") from error


def _text_list(value: object, *, where: str) -> list[str]:
    """Проверить, что значение — список непустых строк.

    Args:
        value: Проверяемое значение.
        where: Описание места для сообщения об ошибке.

    Returns:
        Список строк.

    Raises:
        FallbackContentError: Если форма не соответствует ожидаемой.
    """
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise FallbackContentError(f"{where}: ожидался список непустых строк")
    return list(value)


def _text(value: object, *, where: str) -> str:
    """Проверить, что значение — непустая строка.

    Args:
        value: Проверяемое значение.
        where: Описание места для сообщения об ошибке.

    Returns:
        Та же строка.

    Raises:
        FallbackContentError: Если значение не строка или пустое.
    """
    if not isinstance(value, str) or not value.strip():
        raise FallbackContentError(f"{where}: ожидалась непустая строка")
    return value


def _scene_entries() -> list[tuple[str, dict]]:
    """Достать список сцен из файла данных.

    Returns:
        Пары маркер и набор частей в исходном порядке.

    Raises:
        FallbackContentError: Если структура файла не соответствует ожидаемой.
    """
    payload = _read_json(SCENES_FILE)
    if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
        raise FallbackContentError(f"{SCENES_FILE}: нет списка сцен")
    entries: list[tuple[str, dict]] = []
    for entry in payload["scenes"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("scene"), dict):
            raise FallbackContentError(f"{SCENES_FILE}: сцена без поля scene")
        entries.append((_text(entry.get("marker"), where=f"{SCENES_FILE}.marker"), entry["scene"]))
    return entries


def _scene_parts(scene: object, *, where: str) -> dict[str, str]:
    """Проверить, что сцена содержит все обязательные части.

    Args:
        scene: Разобранная сцена.
        where: Описание места для сообщения об ошибке.

    Returns:
        Словарь частей сцены.

    Raises:
        FallbackContentError: Если не хватает какого-то поля.
    """
    if not isinstance(scene, dict):
        raise FallbackContentError(f"{where}: ожидался объект сцены")
    absent = [field for field in SCENE_FIELDS if field not in scene]
    if absent:
        raise FallbackContentError(f"{where}: нет частей {absent}")
    return {field: _text(scene[field], where=f"{where}.{field}") for field in SCENE_FIELDS}


@lru_cache(maxsize=1)
def card_library() -> dict[str, tuple[FallbackCard, ...]]:
    """Библиотека заготовочных карточек по трекам.

    Порядок карточек внутри трека значим: заготовочная генерация берёт их сверху
    вниз и останавливается на размере партии.

    Returns:
        Словарь имени трека к списку карточек.

    Raises:
        FallbackContentError: Если данные неполные или испорчены.
    """
    payload = _read_json(CARDS_FILE)
    if not isinstance(payload, dict):
        raise FallbackContentError(f"{CARDS_FILE}: ожидался объект с ключами треков")

    missing = [track for track in REQUIRED_TRACKS if track not in payload]
    if missing:
        raise FallbackContentError(f"{CARDS_FILE}: нет треков {missing}")

    library: dict[str, tuple[FallbackCard, ...]] = {}
    for track, entries in payload.items():
        if not isinstance(entries, list) or not entries:
            raise FallbackContentError(f"{CARDS_FILE}: трек {track} пуст")
        cards: list[FallbackCard] = []
        for index, entry in enumerate(entries):
            where = f"{CARDS_FILE}: {track}[{index}]"
            if not isinstance(entry, dict):
                raise FallbackContentError(f"{where} не объект")
            cards.append(
                FallbackCard(
                    topic=_text(entry.get("topic"), where=f"{where}.topic"),
                    explanation=_text(entry.get("explanation"), where=f"{where}.explanation"),
                    examples=_text_list(entry.get("examples", []), where=f"{where}.examples"),
                    key_terms=_text_list(entry.get("key_terms", []), where=f"{where}.key_terms"),
                )
            )
        library[track] = tuple(cards)
    return library


@lru_cache(maxsize=1)
def language_scenes() -> tuple[tuple[str, dict[str, str]], ...]:
    """Языковые сцены в порядке приоритета выбора.

    Порядок значим: выбор делает первое совпадение маркера, и перестановка
    изменила бы результат для заголовков, подходящих нескольким сценам сразу.

    Returns:
        Кортеж пар маркер и набор частей сцены.

    Raises:
        FallbackContentError: Если данные неполные или испорчены.
    """
    return tuple(
        (marker, _scene_parts(scene, where=f"{SCENES_FILE}::{marker}"))
        for marker, scene in _scene_entries()
    )


@lru_cache(maxsize=1)
def default_language_scene() -> dict[str, str]:
    """Запасная языковая сцена, когда не подошла ни одна по маркеру.

    Returns:
        Набор частей сцены.

    Raises:
        FallbackContentError: Если запасной сцены нет в данных.
    """
    payload = _read_json(SCENES_FILE)
    if not isinstance(payload, dict) or not isinstance(payload.get("default"), dict):
        raise FallbackContentError(f"{SCENES_FILE}: нет запасной сцены")
    return _scene_parts(payload["default"], where=f"{SCENES_FILE}::default")


def ensure_available() -> None:
    """Проверить, что весь заготовочный контент читается и полон.

    Вызывается при сборке клиента, чтобы битый или удалённый файл данных был
    виден сразу, а не в момент, когда модель уже недоступна и заготовки —
    единственное, что остаётся показать пользователю.

    Raises:
        FallbackContentError: Если контент недоступен или неполон.
    """
    card_library()
    language_scenes()
    default_language_scene()
