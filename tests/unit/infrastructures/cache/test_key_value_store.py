"""
Юнит-тесты KeyValueStore в memory-only режиме (redis_url=None).

Проверяются: отсутствие значения по отсутствующему ключу, инкремент
счётчика и namespace-префиксация ключей.
"""

from src.infrastructures.cache import KeyValueStore


class TestKeyValueStoreMemoryOnly:
    """Группа тестов in-memory фолбэка хранилища."""

    async def test_get_json_returns_none_for_missing_key(self) -> None:
        """
        Тестируем: чтение значения по несуществующему ключу.
        Отдаём: хранилище без записей и произвольный ключ.
        Ожидаем: get_json возвращает None без исключений.
        """
        store = KeyValueStore(redis_url=None, namespace="test-kv")

        assert await store.get_json("missing") is None

    async def test_incr_builds_sequence_per_key(self) -> None:
        """
        Тестируем: инкремент счётчика в памяти.
        Отдаём: хранилище и окно 60 секунд.
        Ожидаем: последовательные вызовы возвращают 1, затем 2.
        """
        store = KeyValueStore(redis_url=None, namespace="test-kv")

        first = await store.incr("counter", expire_seconds=60)
        second = await store.incr("counter", expire_seconds=60)

        assert (first, second) == (1, 2)

    async def test_namespace_prefixes_keys(self) -> None:
        """
        Тестируем: namespace-префиксацию внутренних ключей.
        Отдаём: два хранилища с разными namespace и одинаковым ключом.
        Ожидаем: значения не пересекаются между namespace.
        """
        first = KeyValueStore(redis_url=None, namespace="ns-one")
        second = KeyValueStore(redis_url=None, namespace="ns-two")
        await first.incr("shared", expire_seconds=60)

        assert await second.get_json("shared") is None
        assert first._make_key("shared") == "ns-one:shared"
