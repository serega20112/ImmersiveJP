
from src.config.base import BaseAppSettings


class RedisSettings(BaseAppSettings):
    """Настройки кеша / Redis."""

    redis_enabled: bool = True
    redis_required: bool = False
    redis_url: str | None = "redis://localhost:6379/0"

    model_config = BaseAppSettings.model_config
