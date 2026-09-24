"""Вынести заготовочный учебный контент из кода в данные.

Текст заготовок жил внутри инфраструктурного модуля LLM-клиента смешанно с
логикой: чтобы поправить формулировку карточки, нужно было правать Python и
проходить ревью кода. Скрипт читает литералы из исходника через AST и пишет их
в JSON-файлы один в один, поэтому перенос не содержит ручного набора и не может
потерять или испортить текст.

Запуск:
    python -m scripts.generate_fallback_content
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

SOURCE_PATH = Path("src/infrastructures/external/llm/fallbacks.py")
OUTPUT_DIR = Path("src/infrastructures/external/llm/fallback_data")
CARD_FIELDS = ("topic", "explanation", "examples", "key_terms")


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    """Найти функцию по имени на верхнем уровне класса миксина.

    Args:
        tree: Разобранное дерево модуля.
        name: Имя функции.

    Returns:
        Узел объявления функции.

    Raises:
        LookupError: Если функция не найдена.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise LookupError(f"Функция {name} не найдена в {SOURCE_PATH}")


def assigned_literal(function: ast.FunctionDef, variable: str) -> Any:
    """Достать значение присваивания локальной переменной-литерала.

    Args:
        function: Узел функции.
        variable: Имя переменной.

    Returns:
        Разобранное значение литерала.

    Raises:
        LookupError: Если присваивания нет.
        ValueError: Если значение не чистый литерал.
    """
    for node in function.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == variable for target in node.targets
        ):
            continue
        try:
            return ast.literal_eval(node.value)
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"{variable} в {function.name} не является литералом") from error
    raise LookupError(f"Присваивание {variable} не найдено в {function.name}")


def returned_literal(function: ast.FunctionDef) -> Any:
    """Достать литерал из последнего return функции.

    Args:
        function: Узел функции.

    Returns:
        Разобранное значение возврата.

    Raises:
        ValueError: Если последний return не является литералом.
    """
    for node in reversed(function.body):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError) as error:
                raise ValueError(f"return в {function.name} не является литералом") from error
    raise ValueError(f"Литеральный return не найден в {function.name}")


def build_card_library(tree: ast.Module) -> dict[str, list[dict[str, Any]]]:
    """Собрать библиотеку карточек в формате данных.

    Args:
        tree: Разобранное дерево модуля.

    Returns:
        Словарь трека к списку карточек с именованными полями.
    """
    library = assigned_literal(function_node(tree, "_fallback_cards"), "library")
    return {
        track: [dict(zip(CARD_FIELDS, entry, strict=True)) for entry in entries]
        for track, entries in library.items()
    }


def build_language_scenes(tree: ast.Module) -> dict[str, Any]:
    """Собрать языковые сцены вместе с запасной сценой.

    Порядок сцен сохраняется: выбор идёт первым совпадением маркера, и перестановка
    изменила бы результат для заголовков, подходящих под несколько маркеров.

    Args:
        tree: Разобранное дерево модуля.

    Returns:
        Словарь со списком сцен и значением по умолчанию.
    """
    function = function_node(tree, "_language_scene_parts")
    scenes = assigned_literal(function, "scenes")
    return {
        "scenes": [{"marker": marker, "scene": scene} for marker, scene in scenes],
        "default": returned_literal(function),
    }


def write_json(path: Path, payload: Any) -> int:
    """Записать JSON-файл с читаемым переносом строк.

    Args:
        path: Куда писать.
        payload: Что сериализовать.

    Returns:
        Количество верхнеуровневых элементов в записанных данных.
    """
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(payload)


def main() -> int:
    """Вычитать литералы из исходника и записать файлы с данными.

    Returns:
        Код завершения: 0 — файлы записаны.
    """
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cards = build_card_library(tree)
    scenes = build_language_scenes(tree)

    card_files = write_json(OUTPUT_DIR / "cards.json", cards)
    scene_count = write_json(OUTPUT_DIR / "language_scenes.json", scenes)

    for track, entries in cards.items():
        print(f"карточки {track}: {len(entries)}")
    print(f"треков в библиотеке: {card_files}")
    print(f"сцен языка: {len(scenes['scenes'])} + запасная, файл на {scene_count} ключа")
    print("RESULT: CONTENT WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
