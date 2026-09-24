"""
E2E-смоук-тесты собранного приложения.

Проверяются: рендер лендинга, доступность статики, наличие /health
и прометеевский срез метрик на реальном create_app (TestClient).
"""

from starlette import status
from starlette.testclient import TestClient

from src.presentation.http.app import create_app


class TestAppSmoke:
    """Группа тестов жизнеспособности собранного приложения."""

    def test_landing_page_renders(self) -> None:
        """
        Тестируем: главную страницу собранного приложения.
        Отдаём: create_app без внешних сервисов (Redis недоступен — фолбэк в память).
        Ожидаем: GET / возвращает 200 и HTML-документ.
        """
        app = create_app()

        with TestClient(app) as client:
            response = client.get("/", follow_redirects=False)

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_static_assets_are_served(self) -> None:
        """
        Тестируем: раздачу статики фронтенда.
        Отдаём: запрос к /static/css/main.css.
        Ожидаем: ответ 200 с CSS-контентом.
        """
        app = create_app()

        with TestClient(app) as client:
            response = client.get("/static/css/main.css", follow_redirects=False)

        assert response.status_code == status.HTTP_200_OK
        assert "text/css" in response.headers["content-type"]

    def test_metrics_endpoint_renders_prometheus_snapshot(self) -> None:
        """
        Тестируем: эндпоинт метрик Prometheus.
        Отдаём: один запрос к лендингу, затем запрос к /metrics.
        Ожидаем: 200; срез содержит счётчик immersjp_http_requests_total
                 с меткой route="/" для учтённого запроса.
        """
        app = create_app()

        with TestClient(app) as client:
            client.get("/", follow_redirects=False)
            response = client.get("/metrics", follow_redirects=False)

        assert response.status_code == status.HTTP_200_OK
        assert "immersjp_http_requests_total" in response.text
        assert 'route="/"' in response.text

    def test_health_endpoint_responds(self) -> None:
        """
        Тестируем: служебный эндпоинт проверки живости.
        Отдаём: запрос к /health без авторизации.
        Ожидаем: ответ 200 (вне зависимости от детального состояния сервисов).
        """
        app = create_app()

        with TestClient(app) as client:
            response = client.get("/health", follow_redirects=False)

        assert response.status_code == status.HTTP_200_OK
