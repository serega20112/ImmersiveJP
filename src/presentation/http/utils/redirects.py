"""Редиректы HTTP-слоя презентации."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse


class RouteRedirectError(Exception):
    """Исключение-сигнал для редиректа из глубины стека обработки запроса."""

    def __init__(self, location: str):
        """Инициализировать исключение редиректа.

        Args:
            location: Адрес, на который нужно перенаправить пользователя.
        """
        super().__init__(location)
        self.location = location


def redirect_to_route(request: Request, route_name: str) -> RedirectResponse:
    """Выполнить редирект на именованный роут.

    Args:
        request: Входящий запрос.
        route_name: Имя роута из реестра маршрутов приложения.

    Returns:
        Редирект-ответ с кодом 303.
    """
    return RedirectResponse(url=request.app.url_path_for(route_name), status_code=303)
