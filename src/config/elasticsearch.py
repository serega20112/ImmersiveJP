
from src.config.base import BaseAppSettings


class ElasticsearchSettings(BaseAppSettings):
    """Настройки Elasticsearch (логгирование/индексация)."""

    elasticsearch_enabled: bool = False
    elasticsearch_url: str | None = None
    elasticsearch_log_index: str = "immersjp-logs"

    model_config = BaseAppSettings.model_config
