"""Юнит-тесты установки и очистки аутентификационных cookie."""

from fastapi.responses import RedirectResponse

from src.config.settings import settings
from src.presentation.http.utils.cookies import clear_auth_cookies, set_auth_cookies


def _response() -> RedirectResponse:
    """Собрать пустой редирект-ответ для проверки cookie.

    Returns:
        RedirectResponse без заголовков cookie.
    """
    return RedirectResponse(url="/", status_code=303)


class TestSetAuthCookies:
    """Группа тестов установки cookie."""

    def test_sets_access_and_refresh_cookies(self) -> None:
        """
        Тестируем: установку пары аутентификационных cookie.
        Отдаём: редирект-ответ и два токена.
        Ожидаем: заголовки Set-Cookie содержат имена из настроек и флаг HttpOnly.
        """
        response = _response()

        set_auth_cookies(response, "access-value", "refresh-value")

        headers = response.headers.getlist("set-cookie")
        assert any(settings.security.access_token_cookie_name in header for header in headers)
        assert any(settings.security.refresh_token_cookie_name in header for header in headers)
        assert all("httponly" in header.lower() for header in headers)
        assert all("path=/;" in header.lower() for header in headers)


class TestClearAuthCookies:
    """Группа тестов очистки cookie."""

    def test_clear_sets_expired_cookies(self) -> None:
        """
        Тестируем: удаление аутентификационных cookie.
        Отдаём: редирект-ответ.
        Ожидаем: Set-Cookie с max-age=0 (или истёкшей датой) для обоих имён.
        """
        response = _response()

        clear_auth_cookies(response)

        headers = response.headers.getlist("set-cookie")
        assert any(settings.security.access_token_cookie_name in header for header in headers)
        assert any(settings.security.refresh_token_cookie_name in header for header in headers)
        assert any("max-age=0" in header.lower() for header in headers)
