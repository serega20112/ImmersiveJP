"""Flash-сообщения, сохраняемые в сессии между запросами."""

from __future__ import annotations

from fastapi import Request


def flash(request: Request, message: str, category: str = "info") -> None:
    """Добавить flash-сообщение в сессию.

    Args:
        request: Входящий запрос.
        message: Текст сообщения.
        category: Категория сообщения (info, success, error).
    """
    queue = list(request.session.get("flash_messages", []))
    queue.append({"message": message, "category": category})
    request.session["flash_messages"] = queue


def pop_flashes(request: Request) -> list[dict[str, str]]:
    """Извлечь и очистить накопленные flash-сообщения.

    Args:
        request: Входящий запрос.

    Returns:
        Список сообщений с категориями.
    """
    messages = list(request.session.get("flash_messages", []))
    request.session["flash_messages"] = []
    return messages
