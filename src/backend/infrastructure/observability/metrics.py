from __future__ import annotations

from collections import Counter, defaultdict
from threading import Lock


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class HttpMetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: Counter[tuple[str, str, str]] = Counter()
        self._duration_sum: defaultdict[tuple[str, str], float] = defaultdict(float)
        self._duration_count: Counter[tuple[str, str]] = Counter()
        self._rate_limited: Counter[str] = Counter()

    def record_request(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        key = (method.upper(), route, str(status_code))
        with self._lock:
            self._requests[key] += 1
            duration_key = (method.upper(), route)
            self._duration_sum[duration_key] += max(duration_ms, 0.0)
            self._duration_count[duration_key] += 1

    def record_rate_limited(self, *, route: str) -> None:
        with self._lock:
            self._rate_limited[route] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            requests = list(self._requests.items())
            duration_sum = dict(self._duration_sum)
            duration_count = dict(self._duration_count)
            rate_limited = list(self._rate_limited.items())

        lines = [
            "# HELP immersjp_http_requests_total Total HTTP requests processed.",
            "# TYPE immersjp_http_requests_total counter",
        ]
        for (method, route, status_code), value in sorted(requests):
            lines.append(
                f'immersjp_http_requests_total{{method="{_escape_label(method)}",route="{_escape_label(route)}",status_code="{_escape_label(status_code)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP immersjp_http_request_duration_ms_sum Total HTTP request duration in milliseconds.",
                "# TYPE immersjp_http_request_duration_ms_sum counter",
            ]
        )
        for (method, route), value in sorted(duration_sum.items()):  # type: ignore[assignment]
            lines.append(
                f'immersjp_http_request_duration_ms_sum{{method="{_escape_label(method)}",route="{_escape_label(route)}"}} {value:.2f}'
            )

        lines.extend(
            [
                "# HELP immersjp_http_request_duration_ms_count Total number of duration samples.",
                "# TYPE immersjp_http_request_duration_ms_count counter",
            ]
        )
        for (method, route), value in sorted(duration_count.items()):
            lines.append(
                f'immersjp_http_request_duration_ms_count{{method="{_escape_label(method)}",route="{_escape_label(route)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP immersjp_http_rate_limited_total Total number of rate-limited requests.",
                "# TYPE immersjp_http_rate_limited_total counter",
            ]
        )
        for route, value in sorted(rate_limited):
            lines.append(
                f'immersjp_http_rate_limited_total{{route="{_escape_label(route)}"}} {value}'
            )

        return "\n".join(lines) + "\n"
