from pydantic import Field

from src.config.base import BaseAppSettings


class RAGSettings(BaseAppSettings):
    """Настройки RAG (retrieval-augmented generation)."""

    rag_chunk_size: int = Field(default=1200)
    rag_chunk_overlap: int = Field(default=150)
    rag_top_k: int = Field(default=3)
    rag_min_score: float = Field(default=0.4)
    rag_embedding_cache_ttl_seconds: int = Field(default=86400)

    model_config = BaseAppSettings.model_config
