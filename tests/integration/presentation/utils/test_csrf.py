"""
Интеграционные тесты проверки CSRF-токенов.

Проверяются: приём совпадающего токена из заголовка и из формы,
отказ при отсутствии токена и сохранение доступности тела формы
для обработчика после проверки.
"""

import pytest
from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from src.application.exceptions import ErrorCode, SecurityViolationError
from src.config.settings import settings
from src.presentation.http.utils.csrf import ensure_csrf_token, validate_csrf


def _build_request(method: str, *, content_type: str = "", headers=None) -> Request:
    """Собрать ASGI-запрос с сессией и опциональным content-type.

    Args:
        method: HTTP-метод запроса.
        content_type: Значение заголовка Content-Type или пустая строка.
        headers: Дополнительные заголовки в формате starlette.

    Returns:
        Объект Request c пустой сессией.
    """
    app = FastAPI()
    scope = {
        "type": "http",
        "app": app,
        "method": method,
        "path": "/",
        "headers": headers or [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("testserver", 80),
        "scheme": "http",
        "session": {},
    }
    if content_type:
        scope["headers"].append((b"content-type", content_type.encode("utf-8")))
    return Request(scope)


class TestValidateCsrf:
    """Группа тестов функции validate_csrf."""

    async def test_accepts_matching_header_token(self) -> None:
        """
        Тестируем: проверку токена, переданного в заголовке.
        Отдаём: POST-запрос с заголовком X-CSRF-Token, содержащим токен сессии.
        Ожидаем: validate_csrf проходит без исключений.
        """
        request = _build_request("POST")
        token = ensure_csrf_token(request)
        header_name = settings.security.csrf_header_name.lower().encode("utf-8")
        request.scope["headers"].append((header_name, token.encode("utf-8")))

        await validate_csrf(request)

    async def test_rejects_missing_token(self) -> None:
        """
        Тестируем: POST-запрос без токена ни в заголовке, ни в форме.
        Отдаём: POST-запрос с пустыми заголовками и без тела.
        Ожидаем: выброс SecurityViolationError с кодом UNAUTHORIZED (403).
        """
        request = _build_request("POST")
        ensure_csrf_token(request)

        with pytest.raises(SecurityViolationError) as exc:
            await validate_csrf(request)

        assert exc.value.code == ErrorCode.UNAUTHORIZED

    async def test_safe_methods_do_not_require_token(self) -> None:
        """
        Тестируем: безопасные методы не требуют подтверждения токеном.
        Отдаём: GET-запрос без заголовков.
        Ожидаем: validate_csrf проходит и выпускает токен в сессию.
        """
        request = _build_request("GET")

        await validate_csrf(request)

        assert ensure_csrf_token(request)


class TestCsrfKeepsFormBody:
    """Группа тестов сохранения тела формы после CSRF-проверки."""

    def test_form_body_available_for_route_handlers(self) -> None:
        """
        Тестируем: доступность полей формы для обработчика после проверки CSRF.
        Отдаём: приложение с middleware-проверкой CSRF, GET отдаёт токен,
                POST отправляет форму с корректным токеном в поле.
        Ожидаем: обработчик получает все поля формы, ответ 200.
        """
        app = FastAPI()

        @app.middleware("http")
        async def csrf_guard(request: Request, call_next):
            await validate_csrf(request)
            return await call_next(request)

        @app.get("/")
        async def index(request: Request):
            return PlainTextResponse(ensure_csrf_token(request))

        @app.post("/submit")
        async def submit(
            email: str = Form(),
            password: str = Form(),
            display_name: str = Form(),
        ):
            return {"email": email, "password": password, "display_name": display_name}

        app.add_middleware(SessionMiddleware, secret_key="test-secret")

        with TestClient(app) as client:
            token = client.get("/").text
            response = client.post(
                "/submit",
                data={
                    "email": "user@example.com",
                    "password": "secret123",
                    "display_name": "Sergey",
                    settings.security.csrf_field_name: token,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "email": "user@example.com",
            "password": "secret123",
            "display_name": "Sergey",
        }
