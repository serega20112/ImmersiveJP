"""Проверить, что все `url_for` из шаблонов ведут на существующие роуты.

Опечатка в имени эндпоинта не ловится ни линтером, ни тестами, которые не
рендерят страницу, и превращается в 500 уже у пользователя. Скрипт собирает
имена из шаблонов и сверяет их с таблицей маршрутов приложения.

Запуск:
    python -m scripts.check_template_routes
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.routing import APIRoute

from src.main import create_app

TEMPLATE_ROOT = Path("src/frontend/templates")
URL_FOR_PATTERN = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")
STATIC_PATTERN = re.compile(r"url_for\(\s*['\"]static['\"]")


def collect_url_names() -> dict[str, list[str]]:
    """Собрать имена эндпоинтов из всех шаблонов.

    Returns:
        Словарь имя эндпоинта -> список файлов, где оно встречается.
    """
    found: dict[str, list[str]] = {}
    for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
        text = template.read_text(encoding="utf-8-sig")
        for match in URL_FOR_PATTERN.finditer(text):
            name = match.group(1)
            if STATIC_PATTERN.match(f"url_for('{name}')"):
                continue
            found.setdefault(name, []).append(str(template))
    return found


def collect_route_names() -> set[str]:
    """Получить имена всех маршрутов приложения.

    Returns:
        Множество зарегистрированных имён эндпоинтов.
    """
    app = create_app()
    return {route.name for route in app.routes if isinstance(route, APIRoute)}


def main() -> int:
    """Сверить имена шаблонов с маршрутами.

    Returns:
        Код завершения: 0 — всё разрешается, 1 — есть битые ссылки.
    """
    url_names = collect_url_names()
    route_names = collect_route_names()
    missing = {name: files for name, files in url_names.items() if name not in route_names}

    print(f"имён url_for в шаблонах : {len(url_names)}")
    print(f"маршрутов в приложении  : {len(route_names)}")

    if not missing:
        print("RESULT: ALL ROUTES RESOLVE")
        return 0

    for name, files in sorted(missing.items()):
        print(f"BROKEN url_for('{name}') в: {', '.join(sorted(set(files)))}")
    print("RESULT: BROKEN LINKS FOUND")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
