from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.backend.dependencies.container import RequestContainer

_request_container_context: ContextVar["RequestContainer | None"] = ContextVar(
    "request_container_context",
    default=None,
)
_UNRESOLVED_CURRENT_USER = object()


def bind_request_container(container: "RequestContainer") -> Token["RequestContainer | None"]:
    return _request_container_context.set(container)


def release_request_container(token: Token["RequestContainer | None"]) -> None:
    _request_container_context.reset(token)


def get_request_container() -> "RequestContainer":
    request_container = _request_container_context.get()
    if request_container is None:
        raise RuntimeError("Request container is not available in the current context")
    return request_container
