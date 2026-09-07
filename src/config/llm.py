from pydantic import Field, field_validator

from src.config.base import BaseAppSettings


class LLMSettings(BaseAppSettings):
    """Настройки LLM/инференс-клиентов (HF router, OpenRouter, embedding)."""

    openrouter_api_key: str | None = None
    embedding_model: str = "text-embedding-ada-002"

    llm_request_limit: int = Field(default=30)
    llm_request_window_seconds: int = Field(default=3600)

    hf_api_token: str | None = None
    hf_model: str = "openai/gpt-oss-120b"
    hf_provider: str | None = "fireworks-ai"
    hf_api_url: str = "https://router.huggingface.co/v1/chat/completions"
    hf_timeout_seconds: float = Field(default=30)
    hf_retry_attempts: int = Field(default=3)
    hf_retry_backoff_seconds: float = Field(default=0.8)

    hf_cards_model: str = "openai/gpt-oss-20b"
    hf_cards_timeout_seconds: float = Field(default=20)
    hf_cards_retry_attempts: int = Field(default=1)
    hf_cards_max_tokens: int = Field(default=1400)
    hf_cards_circuit_open_seconds: int = Field(default=180)

    hf_mentor_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_mentor_timeout_seconds: float = Field(default=18)
    hf_mentor_retry_attempts: int = Field(default=1)
    hf_mentor_max_tokens: int = Field(default=220)

    hf_speech_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_speech_timeout_seconds: float = Field(default=18)
    hf_speech_retry_attempts: int = Field(default=1)
    hf_speech_max_tokens: int = Field(default=420)

    hf_work_review_model: str = "openai/gpt-oss-20b:fireworks-ai"
    hf_work_review_timeout_seconds: float = Field(default=14)
    hf_work_review_retry_attempts: int = Field(default=1)
    hf_work_review_max_tokens: int = Field(default=700)

    model_config = BaseAppSettings.model_config

    @field_validator(
        "llm_request_limit",
        "llm_request_window_seconds",
        "hf_cards_retry_attempts",
        "hf_cards_max_tokens",
        "hf_cards_circuit_open_seconds",
        "hf_work_review_retry_attempts",
        "hf_work_review_max_tokens",
    )
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Numeric limits must be greater than zero")
        return value

    @field_validator(
        "hf_cards_timeout_seconds",
        "hf_mentor_timeout_seconds",
        "hf_speech_timeout_seconds",
        "hf_work_review_timeout_seconds",
        "hf_timeout_seconds",
        "hf_retry_backoff_seconds",
    )
    @classmethod
    def validate_positive_floats(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Timeouts and backoff must be greater than zero")
        return value
