from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(slots=True)
class ApplicationError(Exception):
    status_code: int
    title: str
    message: str
    event: str = "http.application_error"
    redirect_on_post: bool = False
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


class SecurityViolationError(ApplicationError):
    def __init__(self, message: str = "Некорректный CSRF token"):
        super().__init__(
            status_code=403,
            title="Запрос отклонен",
            message=message,
            event="http.security_violation",
            redirect_on_post=True,
        )


class RateLimitExceededError(ApplicationError):
    def __init__(
        self,
        *,
        limit: int,
        remaining: int,
        retry_after_seconds: int,
        message: str = "Слишком много запросов. Подожди немного и повтори.",
    ):
        super().__init__(
            status_code=429,
            title="Слишком много запросов",
            message=message,
            event="http.rate_limited",
            headers={
                "Retry-After": str(retry_after_seconds),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(max(remaining, 0)),
                "X-RateLimit-Window": str(retry_after_seconds),
            },
        )
