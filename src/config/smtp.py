from pydantic import Field

from src.config.base import BaseAppSettings


class SMTPSettings(BaseAppSettings):
    """Настройки SMTP-почты."""

    smtp_host: str | None = None
    smtp_port: int = Field(default=587)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = Field(default="noreply@immersjp.local")
    smtp_use_tls: bool = True

    model_config = BaseAppSettings.model_config
