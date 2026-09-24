"""Юнит-тесты AppSettings и SecuritySettings: валидаторы значений."""

import pytest
from pydantic import ValidationError

from src.config.app import AppSettings
from src.config.security import SecuritySettings


class TestAppSettings:
    """Группа тестов основных настроек приложения."""

    def test_defaults_are_stable(self) -> None:
        """
        Тестируем: значения по умолчанию.
        Отдаём: AppSettings без аргументов.
        Ожидаем: имя ImmersJP, порт 8000, метрики и лимитер включены.
        """
        settings_model = AppSettings()

        assert settings_model.app_name == "ImmersJP"
        assert settings_model.app_port == 8000
        assert settings_model.metrics_enabled is True
        assert settings_model.api_rate_limit_enabled is True

    @pytest.mark.parametrize(
        "field",
        ["onboarding_page_cache_ttl_seconds", "api_rate_limit_requests", "api_rate_limit_window_seconds"],
    )
    def test_rejects_non_positive_limits(self, field: str) -> None:
        """
        Тестируем: запрет неположительных лимитов.
        Отдаём: 0 и -5 в каждое числовое поле.
        Ожидаем: ValidationError для каждого варианта.
        """
        with pytest.raises(ValidationError):
            AppSettings(**{field: 0})
        with pytest.raises(ValidationError):
            AppSettings(**{field: -5})


class TestSecuritySettings:
    """Группа тестов настроек безопасности."""

    def test_secrets_are_stripped(self) -> None:
        """
        Тестируем: нормализацию секретов.
        Отдаём: ключи с пробелами по краям.
        Ожидаем: значения обрезаны.
        """
        settings_model = SecuritySettings(secret_key="  k1  ", session_secret="  k2  ")

        assert settings_model.secret_key == "k1"
        assert settings_model.session_secret == "k2"

    def test_csrf_names_have_sane_defaults(self) -> None:
        """
        Тестируем: имена CSRF-полей и заголовков по умолчанию.
        Отдаём: SecuritySettings без аргументов.
        Ожидаем: поле и сессионный ключ "csrf_token", заголовок X-CSRF-Token.
        """
        settings_model = SecuritySettings()

        assert settings_model.csrf_field_name == "csrf_token"
        assert settings_model.csrf_session_key == "csrf_token"
        assert settings_model.csrf_header_name == "X-CSRF-Token"

    @pytest.mark.parametrize("allowed", ["lax", "strict", "none"])
    def test_accepts_known_samesite(self, allowed: str) -> None:
        """
        Тестируем: допустимые значения samesite.
        Отдаём: lax, strict, none (в любом регистре).
        Ожидаем: значение нормализовано к нижнему регистру.
        """
        settings_model = SecuritySettings(cookie_samesite=allowed.upper())

        assert settings_model.cookie_samesite == allowed

    def test_rejects_unknown_samesite(self) -> None:
        """
        Тестируем: недопустимое значение samesite.
        Отдаём: "always".
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            SecuritySettings(cookie_samesite="always")

    @pytest.mark.parametrize("field", ["access_token_expire_minutes", "refresh_token_expire_days", "email_verification_expire_minutes"])
    def test_rejects_non_positive_expires(self, field: str) -> None:
        """
        Тестируем: запрет неположительных сроков жизни токенов.
        Отдаём: 0 в каждое поле.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            SecuritySettings(**{field: 0})
