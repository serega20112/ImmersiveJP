from pydantic import Field, model_validator

from src.config.base import BaseAppSettings


def _build_database_url(
    *,
    user: str,
    password: str,
    host: str,
    port: int | str,
    database: str,
    async_mode: bool,
) -> str:
    scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def _normalize_database_url(value: str | None, *, async_mode: bool) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        raise ValueError("Database URL normalization requires a non-empty value")
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://') :]}"
    if async_mode:
        if raw_value.startswith("postgresql+asyncpg://"):
            return raw_value
        if raw_value.startswith("postgresql+psycopg://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql+psycopg://') :]}"
        if raw_value.startswith("postgresql://"):
            return f"postgresql+asyncpg://{raw_value[len('postgresql://') :]}"
        return raw_value
    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value
    if raw_value.startswith("postgresql+asyncpg://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql+asyncpg://') :]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql://') :]}"
    return raw_value


class DatabaseSettings(BaseAppSettings):
    """Настройки подключения к базе данных PostgreSQL."""

    postgres_user: str = "immersjp"
    postgres_password: str = "immersjp"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "immersjp"
    database_url: str | None = None
    database_sync_url: str | None = None

    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=40)

    model_config = BaseAppSettings.model_config

    @model_validator(mode="after")
    def normalize_database_urls(self) -> "DatabaseSettings":
        fallback_database_url = _build_database_url(
            user=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            async_mode=False,
        )
        raw_database_url = self.database_url or self.database_sync_url or fallback_database_url
        self.database_url = _normalize_database_url(
            self.database_url or raw_database_url,
            async_mode=True,
        )
        self.database_sync_url = _normalize_database_url(
            self.database_sync_url or raw_database_url,
            async_mode=False,
        )
        return self
