"""Юнит-тесты редиректов HTTP-слоя (utils/redirects)."""

import pytest
from fastapi import FastAPI, Request
from starlette.routing import NoMatchFound

from src.presentation.http.utils.redirects import RouteRedirectError, redirect_to_route


def _request_with_app() -> Request:
    """Собрать Request с приложением, содержащим именованный роут.

    Returns:
        Объект Request с маршрутом "test.target".
    """
    app = FastAPI()

    @app.get("/target", name="test.target")
    async def _target():
        return {}

    scope = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


class TestRouteRedirectError:
    """Группа тестов исключения-сигнала редиректа."""

    def test_stores_location(self) -> None:
        """
        Тестируем: хранение адреса перенаправления.
        Отдаём: строку пути.
        Ожидаем: исключение носит путь в атрибуте location.
        """
        error = RouteRedirectError("/auth/login")

        assert error.location == "/auth/login"


class TestRedirectToRoute:
    """Группа тестов редиректа на именованный маршрут."""

    def test_returns_303_to_route_path(self) -> None:
        """
        Тестируем: редирект на путь именованного маршрута.
        Отдаём: запрос к приложению с маршрутом "test.target".
        Ожидаем: RedirectResponse со статусом 303 и адресом /target.
        """
        response = redirect_to_route(_request_with_app(), "test.target")

        assert response.status_code == 303
        assert response.headers["location"] == "/target"

    def test_raises_for_unknown_route(self) -> None:
        """
        Тестируем: обращение к несуществующему имени маршрута.
        Отдаём: несуществующее имя маршрута.
        Ожидаем: NoMatchFound от url_path_for.
        """
        with pytest.raises(NoMatchFound):
            redirect_to_route(_request_with_app(), "missing.route")
