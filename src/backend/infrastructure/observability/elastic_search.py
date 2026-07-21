from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any

from elasticsearch import AsyncElasticsearch

from src.backend.dependencies.settings import Settings


class ElasticsearchLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._client: AsyncElasticsearch | None = None
        self._index = Settings.elasticsearch_log_index

    async def _ensure_client(self) -> AsyncElasticsearch | None:
        if self._client is not None:
            return self._client
        url = Settings.elasticsearch_url
        if not url:
            return None
        self._client = AsyncElasticsearch(hosts=[url])
        return self._client

    def emit(self, record: logging.LogRecord) -> None:
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._async_emit(record))
        except RuntimeError:
            pass

    async def _async_emit(self, record: logging.LogRecord) -> None:
        client = await self._ensure_client()
        if client is None:
            return
        document: dict[str, Any] = {
            "@timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
        }
        event = getattr(record, "event", None)
        if event:
            document["event"] = event
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            document.update(extra_fields)
        with contextlib.suppress(Exception):
            await client.index(index=self._index, document=document)

    async def close_client(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
