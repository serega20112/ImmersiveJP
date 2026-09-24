"""Юнит-тесты реального RateLimiter поверх memory-only KeyValueStore."""

import pytest

from src.infrastructures.cache import KeyValueStore
from src.infrastructures.security.rate_limiter import RateLimiter


@pytest.fixture
def limiter() -> RateLimiter:
    """RateLimiter на in-memory хранилище."""
    return RateLimiter(KeyValueStore(redis_url=None, namespace="test-limiter"))


class TestRateLimiter:
    """Группа тестов счётчика ограничения частоты."""

    async def test_consume_increments_counter(self, limiter: RateLimiter) -> None:
        """
        Тестируем: последовательное потребление квоты.
        Отдаём: три вызова consume с одним ключом.
        Ожидаем: счётчик 1, 2, 3.
        """
        first = await limiter.consume("http-api", "1.2.3.4", window_seconds=60)
        second = await limiter.consume("http-api", "1.2.3.4", window_seconds=60)
        third = await limiter.consume("http-api", "1.2.3.4", window_seconds=60)

        assert (first, second, third) == (1, 2, 3)

    async def test_keys_are_isolated_per_ip(self, limiter: RateLimiter) -> None:
        """
        Тестируем: изоляцию счётчиков разных клиентов.
        Отдаём: consume от двух разных IP.
        Ожидаем: у каждого свой счётчик с единицы.
        """
        first_ip = await limiter.consume("http-api", "1.1.1.1", window_seconds=60)
        second_ip = await limiter.consume("http-api", "2.2.2.2", window_seconds=60)

        assert (first_ip, second_ip) == (1, 1)

    async def test_is_allowed_within_limit(self, limiter: RateLimiter) -> None:
        """
        Тестируем: пропуск запросов в пределах лимита.
        Отдаём: лимит 2 и три запроса подряд.
        Ожидаем: первые два разрешены, третий — нет.
        """
        results = [await limiter.is_allowed("scope", "ip", limit=2, window_seconds=60) for _ in range(3)]

        assert results == [True, True, False]
