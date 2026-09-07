"""Общие вспомогательные функции middleware."""

from __future__ import annotations

from fastapi import Request


def is_static_request(request: Request) -> bool:
    """Определить, относится ли запрос к статическим ресурсам.

    Args:
        request: Входящий запрос.

    Returns:
        True, если запрос обслуживается статикой или favicon.
    """
    return request.url.path.startswith("/static") or request.url.path == "/favicon.ico"


def resolve_route_label(request: Request) -> str:
    """Определить метку маршрута для метрик.

    Args:
        request: Входящий запрос.

    Returns:
        Шаблон пути маршрута либо фактический путь запроса.
    """
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return str(route_path)
    return request.url.path or "/"


def resolve_user_id(request: Request) -> int | None:
    """Определить идентификатор текущего пользователя запроса.

    Args:
        request: Входящий запрос.

    Returns:
        Идентификатор пользователя или None.
    """
    current_user = getattr(request.state, "current_user", None)
    return getattr(current_user, "id", None)
