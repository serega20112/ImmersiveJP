"""Юнит-тесты вспомогательных функций middleware (_helpers)."""

from fastapi import FastAPI, Request

from src.presentation.http.middleware._helpers import (
    is_static_request,
    resolve_route_label,
    resolve_user_id,
)


def _request(path: str, *, route_path: str | None = None, current_user: object = None) -> Request:
    """Собрать Request с путём, опциональным маршрутом и пользователем.

    Args:
        path: Путь запроса.
        route_path: Путь сопоставленного маршрута (scope["route"]).
        current_user: Объект пользователя в request.state.

    Returns:
        Объект Request для проверки helper-функций.
    """
    scope: dict = {
        "type": "http",
        "app": FastAPI(),
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    if route_path is not None:
        scope["route"] = type("Route", (), {"path": route_path})()
    request = Request(scope)
    request.state.current_user = current_user
    return request


class TestIsStaticRequest:
    """Группа тестов определения статических запросов."""

    def test_static_prefix_and_favicon_are_static(self) -> None:
        """
        Тестируем: признаки статических запросов.
        Отдаём: пути /static/... и /favicon.ico.
        Ожидаем: оба распознаны как статические.
        """
        assert is_static_request(_request("/static/css/main.css")) is True
        assert is_static_request(_request("/favicon.ico")) is True

    def test_dynamic_paths_are_not_static(self) -> None:
        """
        Тестируем: динамические маршруты.
        Отдаём: пути / и /metrics, а также /statics (префикс /static совпадает).
        Ожидаем: / и /metrics не статические; /statics считается статическим
                 из-за префиксного сравнения — фиксируем текущее поведение.
        """
        assert is_static_request(_request("/")) is False
        assert is_static_request(_request("/metrics")) is False
        assert is_static_request(_request("/statics")) is True


class TestResolveRouteLabel:
    """Группа тестов метки маршрута для метрик."""

    def test_uses_matched_route_path(self) -> None:
        """
        Тестируем: метку по сопоставленному маршруту.
        Отдаём: запрос с scope["route"].path = "/learn/{track}".
        Ожидаем: шаблон маршрута вместо фактического пути.
        """
        assert resolve_route_label(_request("/learn/language", route_path="/learn/{track}")) == "/learn/{track}"

    def test_falls_back_to_request_path(self) -> None:
        """
        Тестируем: метку без сопоставленного маршрута.
        Отдаём: запрос без scope["route"].
        Ожидаем: фактический путь запроса.
        """
        assert resolve_route_label(_request("/somewhere")) == "/somewhere"


class TestResolveUserId:
    """Группа тестов извлечения идентификатора пользователя."""

    def test_returns_user_id(self) -> None:
        """
        Тестируем: извлечение id текущего пользователя.
        Отдаём: объект с id=7 в request.state.current_user.
        Ожидаем: 7.
        """
        assert resolve_user_id(_request("/", current_user=type("U", (), {"id": 7})())) == 7

    def test_returns_none_for_anonymous(self) -> None:
        """
        Тестируем: отсутствие пользователя.
        Отдаём: current_user=None.
        Ожидаем: None.
        """
        assert resolve_user_id(_request("/", current_user=None)) is None
