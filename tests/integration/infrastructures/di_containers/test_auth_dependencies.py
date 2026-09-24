"""
Интеграционные тесты зависимостей аутентификации DI-контейнера.

Проверяются переходы require_*-зависимостей: редиректы для анонимного
пользователя, возврат текущего пользователя и редирект на онбординг,
когда профиль не завершён.
"""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
    require_registered_user,
)
from src.presentation.http import RouteRedirectError


def _build_request(current_user: UserViewDTO | None) -> Request:
    """Собрать ASGI-запрос с именованными роутами и текущим пользователем.

    Args:
        current_user: Пользователь в request.state или None для анонима.

    Returns:
        Объект Request с приложением, содержащим именованные роуты.
    """
    app = FastAPI()

    @app.get("/auth/login", name="auth.login_page")
    async def _login():
        return {}

    @app.get("/auth/register", name="auth.register_page")
    async def _register():
        return {}

    @app.get("/onboarding", name="onboarding.page")
    async def _onboarding():
        return {}

    scope = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    request = Request(scope)
    request.state.current_user = current_user
    return request


class TestAuthDependencies:
    """Группа тестов require_*-зависимостей доступа."""

    async def test_require_registered_user_redirects_to_register(self) -> None:
        """
        Тестируем: доступ к странице для неавторизованного (не зарегистрированного) пользователя.
        Отдаём: запрос без текущего пользователя.
        Ожидаем: RouteRedirectError с адресом страницы регистрации.
        """
        request = _build_request(None)

        with pytest.raises(RouteRedirectError) as exc:
            await require_registered_user(request)

        assert exc.value.location == "/auth/register"

    async def test_require_authenticated_user_redirects_to_login(self) -> None:
        """
        Тестируем: доступ к защищённой странице для анонимного пользователя.
        Отдаём: запрос без текущего пользователя.
        Ожидаем: RouteRedirectError с адресом страницы входа.
        """
        request = _build_request(None)

        with pytest.raises(RouteRedirectError) as exc:
            await require_authenticated_user(request)

        assert exc.value.location == "/auth/login"

    async def test_require_authenticated_user_returns_current_user(self) -> None:
        """
        Тестируем: возврат текущего пользователя авторизованного запроса.
        Отдаём: запрос с заполненным request.state.current_user.
        Ожидаем: зависимость возвращает тот же объект пользователя.
        """
        current_user = SimpleNamespace(id=7, onboarding_completed=False)
        request = _build_request(current_user)

        resolved = await require_authenticated_user(request)

        assert resolved is current_user

    async def test_require_onboarded_user_redirects_when_profile_not_finished(self) -> None:
        """
        Тестируем: доступ к защищённой странице без завершённого онбординга.
        Отдаём: пользователь с onboarding_completed=False.
        Ожидаем: RouteRedirectError с адресом страницы онбординга.
        """
        current_user = SimpleNamespace(id=11, onboarding_completed=False)
        request = _build_request(current_user)

        with pytest.raises(RouteRedirectError) as exc:
            await require_onboarded_user(request)

        assert exc.value.location == "/onboarding"

    async def test_require_onboarded_user_returns_user_when_onboarded(self) -> None:
        """
        Тестируем: доступ пользователя с завершённым онбордингом.
        Отдаём: UserViewDTO с onboarding_completed=True.
        Ожидаем: зависимость возвращает того же пользователя без редиректа.
        """
        current_user = UserViewDTO(
            id=3,
            email="user@example.com",
            display_name="Сергей",
            is_email_verified=True,
            onboarding_completed=True,
        )
        request = _build_request(current_user)

        resolved = await require_onboarded_user(request)

        assert resolved is current_user
        assert resolved.onboarding_completed is True
