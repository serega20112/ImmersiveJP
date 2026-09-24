"""Проверить, что ссылки на маршруты и на шаблоны не битые.

Опечатка в имени эндпоинта не ловится ни линтером, ни тестами, которые не
рендерят страницу, и превращается в 500 уже у пользователя. Скрипт сверяет три
вещи: имена `url_for` из шаблонов с маршрутами приложения; имена шаблонов из
роутов с файлами на диске; и `extends`/`include`/`import` внутри шаблонов — тоже
с файлами на диске.

Последняя проверка не заменима компиляцией Jinja: `get_template` сборку
родительского шаблона не выполняет вложенные шаблоны, отсутствующее
{% include %} всплывает только при рендере. То есть ровно тот момент, когда
страницу уже открыли.

Запуск:
    python -m scripts.check_template_routes
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.routing import APIRoute

from src.main import create_app

TEMPLATE_ROOT = Path("src/frontend/templates")
SOURCE_ROOT = Path("src")
URL_FOR_PATTERN = re.compile(r"""url_for\(\s*['"]([^'"]+)['"]""")
TEMPLATE_REFERENCE_PATTERN = re.compile(r"""(?:extends|include|import)\s+["']([^"']+)["']""")
RENDER_TEMPLATE_PATTERN = re.compile(
    r"""render_template\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*["']([^"']+)["']"""
)
STATIC_ENDPOINT_NAME = "static"


def collect_url_names() -> dict[str, list[str]]:
    """Собрать имена эндпоинтов из всех шаблонов.

    Служебное имя `static` исключается: оно принадлежит монтированию статики,
    а не APIRoute, и по своей природе не участвует в сверке с маршрутами.

    Returns:
        Словарь имя эндпоинта -> список файлов, где оно встречается.
    """
    found: dict[str, list[str]] = {}
    for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
        for match in URL_FOR_PATTERN.finditer(_read(template)):
            if match.group(1) == STATIC_ENDPOINT_NAME:
                continue
            found.setdefault(match.group(1), []).append(str(template))
    return found


def collect_route_names() -> set[str]:
    """Получить имена всех маршрутов приложения.

    Returns:
        Множество зарегистрированных имён эндпоинтов.
    """
    app = create_app()
    return {route.name for route in app.routes if isinstance(route, APIRoute)}


def _read(path: Path) -> str:
    """Прочитать файл, терпя BOM в начале.

    Args:
        path: Путь к файлу.

    Returns:
        Содержание файла.
    """
    return path.read_text(encoding="utf-8-sig")


def check_template_references() -> list[str]:
    """Проверить, что все шаблоны и включенные части существуют на диске.

    Returns:
        Описания проблем; пустой список, если висячих ссылок нет.
    """
    problems: list[str] = []

    for source in sorted(SOURCE_ROOT.rglob("*.py")):
        for match in RENDER_TEMPLATE_PATTERN.finditer(_read(source)):
            name = match.group(1)
            if not (TEMPLATE_ROOT / name).is_file():
                problems.append(f"{source}: рендерит отсутствующий шаблон {name!r}")

    for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
        for match in TEMPLATE_REFERENCE_PATTERN.finditer(_read(template)):
            name = match.group(1)
            if not (TEMPLATE_ROOT / name).is_file():
                problems.append(f"{template}: ссылается на отсутствующий {name!r}")

    return problems


def main() -> int:
    """Сверить имена шаблонов с маршрутами и проверить висячие ссылки.

    Returns:
        Код завершения: 0 — всё разрешается, 1 — есть обрывы.
    """
    url_names = collect_url_names()
    route_names = collect_route_names()
    missing_routes = {name: files for name, files in url_names.items() if name not in route_names}
    reference_problems = check_template_references()

    print(f"имён url_for в шаблонах : {len(url_names)}")
    print(f"маршрутов в приложении  : {len(route_names)}")
    print(f"шаблонов в дереве       : {len(list(TEMPLATE_ROOT.rglob('*.html')))}")

    for name, files in sorted(missing_routes.items()):
        print(f"BROKEN url_for('{name}') в: {', '.join(sorted(set(files)))}")
    for problem in reference_problems:
        print(f"BROKEN ссылка: {problem}")

    if missing_routes or reference_problems:
        print("RESULT: BROKEN LINKS OR TEMPLATES FOUND")
        return 1

    print("RESULT: ALL ROUTES AND TEMPLATES RESOLVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
