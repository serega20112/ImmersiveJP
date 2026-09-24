"""Юнит-тесты прометеевского сборщика HTTP-метрик."""

from src.infrastructures.observability.metrics import HttpMetricsCollector, _escape_label


class TestHttpMetricsCollector:
    """Группа тестов сборщика метрик."""

    def test_renders_requests_counter_with_labels(self) -> None:
        """
        Тестируем: рендер счётчика запросов.
        Отдаём: два запроса с разными статусами на один маршрут.
        Ожидаем: два временных ряда с method/route/status_code и корректными значениями.
        """
        collector = HttpMetricsCollector()
        collector.record_request(method="GET", route="/", status_code=200, duration_ms=12.5)
        collector.record_request(method="GET", route="/", status_code=500, duration_ms=3.0)

        output = collector.render_prometheus()

        assert 'immersjp_http_requests_total{method="GET",route="/",status_code="200"} 1' in output
        assert 'immersjp_http_requests_total{method="GET",route="/",status_code="500"} 1' in output

    def test_duration_sum_and_count(self) -> None:
        """
        Тестируем: накопление длительности.
        Отдаём: три запроса с длительностями 10, 20 и 30 мс.
        Ожидаем: sum=60.00 и count=3.
        """
        collector = HttpMetricsCollector()
        for duration in (10.0, 20.0, 30.0):
            collector.record_request(method="POST", route="/api", status_code=200, duration_ms=duration)

        output = collector.render_prometheus()

        assert 'immersjp_http_request_duration_ms_sum{method="POST",route="/api"} 60.00' in output
        assert 'immersjp_http_request_duration_ms_count{method="POST",route="/api"} 3' in output

    def test_rate_limited_counter(self) -> None:
        """
        Тестируем: счётчик лимитированных запросов.
        Отдаём: два события rate limit на одном маршруте.
        Ожидаем: immersjp_http_rate_limited_total со значением 2.
        """
        collector = HttpMetricsCollector()
        collector.record_rate_limited(route="/ping")
        collector.record_rate_limited(route="/ping")

        assert 'immersjp_http_rate_limited_total{route="/ping"} 2' in collector.render_prometheus()

    def test_negative_duration_clamped_to_zero(self) -> None:
        """
        Тестируем: отрицательную длительность.
        Отдаём: duration_ms=-5.
        Ожидаем: в сумму попадает 0.
        """
        collector = HttpMetricsCollector()
        collector.record_request(method="GET", route="/", status_code=200, duration_ms=-5)

        assert 'immersjp_http_request_duration_ms_sum{method="GET",route="/"} 0.00' in collector.render_prometheus()


class TestEscapeLabel:
    """Группа тестов экранирования значений меток."""

    def test_escapes_special_characters(self) -> None:
        """
        Тестируем: экранирование спецсимволов.
        Отдаём: строка с обратным слешем, кавычкой и переводом строки.
        Ожидаем: значения с экранированными символами.
        """
        assert _escape_label('a\\b"c\nd') == 'a\\\\b\\"c\\nd'
