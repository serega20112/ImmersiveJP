from pydantic import Field, field_validator

from src.config.base import BaseAppSettings


class AppSettings(BaseAppSettings):
    """Основные настройки приложения."""

    app_name: str = "ImmersJP"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_base_url: str = "http://127.0.0.1:8000"
    log_level: str = "INFO"

    metrics_enabled: bool = True
    onboarding_page_cache_ttl_seconds: int = Field(default=900)
    text_input_limit: int = Field(default=500)

    api_rate_limit_enabled: bool = True
    api_rate_limit_requests: int = Field(default=240)
    api_rate_limit_window_seconds: int = Field(default=60)

    # Имена полей совпадают с переменными окружения (APP_*), поэтому префикс не нужен
    model_config = BaseAppSettings.model_config

    @field_validator(
        "onboarding_page_cache_ttl_seconds",
        "api_rate_limit_requests",
        "api_rate_limit_window_seconds",
    )
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Numeric limits must be greater than zero")
        return value
