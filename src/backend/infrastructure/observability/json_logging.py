from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_DEFAULT_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}
_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event:
            payload["event"] = event

        extra_fields = getattr(record, "extra_fields", {})
        if isinstance(extra_fields, dict):
            payload.update(self._normalize_mapping(extra_fields))

        payload.update(
            self._normalize_mapping(
                {
                    key: value
                    for key, value in record.__dict__.items()
                    if key not in _DEFAULT_RECORD_FIELDS
                    and key not in {"event", "extra_fields"}
                    and not key.startswith("_")
                }
            )
        )

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

    def _normalize_mapping(self, values: dict[str, Any]) -> dict[str, Any]:
        return {key: self._normalize_value(value) for key, value in values.items()}

    def _normalize_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, dict):
            return {str(key): self._normalize_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_value(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)


def configure_logging(level_name: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = getattr(logging, str(level_name).upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(level)
        logger.addHandler(handler)
        logger.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    logger.log(level, message, extra={"event": event, "extra_fields": fields})
