"""
Юнит-тесты кэширования и single-flight генерации карточек.

Проверяются правила, введённые после того, как одна сетевая осечка превращалась
в шаблонный контент на сутки: заготовка не должна попадать в кэш, повторный
одинаковый запрос не должен дважды уходить в модель, а попадание в кэш обязано
честно считаться ответом модели.
"""

from __future__ import annotations

import asyncio

from src.application.dto.learning import GeneratedCardBatchDTO, GeneratedCardDraftDTO
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.cache import KeyValueStore
from src.infrastructures.external.llm.client import HuggingFaceLLMClient
from src.infrastructures.external.llm.requests import LLMCallResult
from tests.fixtures.factories.user_factory import UserFactory

BATCH_SIZE = 5


def draft(topic: str) -> GeneratedCardDraftDTO:
    """Собрать черновик карточки.

    Args:
        topic: Тема карточки.

    Returns:
        Черновик с минимальным содержимым.
    """
    return GeneratedCardDraftDTO(
        topic=topic,
        explanation=f"Объяснение {topic}",
        examples=["水 | mizu | вода"],
        key_terms=["水"],
    )


def model_batch() -> GeneratedCardBatchDTO:
    """Собрать партию, целиком пришедшую от модели.

    Returns:
        Партию из пяти черновиков.
    """
    drafts = [draft(f"Тема {index}") for index in range(1, BATCH_SIZE + 1)]
    return GeneratedCardBatchDTO(drafts=drafts, model_count=len(drafts), fallback_count=0)


def fallback_batch() -> GeneratedCardBatchDTO:
    """Собрать партию целиком из заготовок.

    Returns:
        Партию из пяти заготовочных черновиков.
    """
    drafts = [draft(f"Заготовка {index}") for index in range(1, BATCH_SIZE + 1)]
    return GeneratedCardBatchDTO(drafts=drafts, model_count=0, fallback_count=len(drafts))


class _Transport:
    """Подмена обращения к модели, считает вызовы и умеет задерживаться."""

    def __init__(self, result: LLMCallResult, gate: asyncio.Event | None = None) -> None:
        """Инициализировать подмену.

        Args:
            result: Ответ, который она возвращает.
            gate: Событие, удерживающее ответ до сигнала.
        """
        self._result = result
        self._gate = gate
        self.calls = 0
        self.payloads: list[dict] = []

    async def __call__(self, payload: dict) -> LLMCallResult:
        """Вернуть заготовленный ответ, засчитав вызов и запомнив контекст.

        Args:
            payload: Контекст генерации.

        Returns:
            Заранее подготовленный результат вызова.
        """
        self.calls += 1
        self.payloads.append(payload)
        if self._gate is not None:
            await self._gate.wait()
        return self._result


def build_client(store_namespace: str) -> HuggingFaceLLMClient:
    """Собрать клиента на in-memory хранилище.

    Args:
        store_namespace: Namespace кэша, изолирующий тесты друг от друга.

    Returns:
        Клиент генерации.
    """
    store = KeyValueStore(redis_url=None, namespace=store_namespace)
    return HuggingFaceLLMClient(store)


async def generate(client: HuggingFaceLLMClient, batch_number: int = 1):
    """Запустить генерацию карточек типовым вызовом.

    Args:
        client: Подменяемый клиент.
        batch_number: Номер партии.

    Returns:
        Результат генерации.
    """
    user = UserFactory().build(user_id=1)
    return await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=batch_number,
        batch_size=BATCH_SIZE,
        previous_topics=[],
    )


class TestCachingRules:
    """Группа тестов правил попадания результата в кэш."""

    async def test_model_batch_is_cached_and_not_requested_twice(self) -> None:
        """
        Тестируем: кэширование ответа модели.
        Отдаём: два одинаковых вызова генерации подряд.
        Ожидаем: модель обращается один раз, второй результат взят из кэша.
        """
        client = build_client("llm-cache-model")
        transport = _Transport(LLMCallResult(model_batch(), generated=True))
        client._request_cards = transport

        first = await generate(client)
        second = await generate(client)

        assert transport.calls == 1
        assert [item.topic for item in first.drafts] == [item.topic for item in second.drafts]

    async def test_fallback_batch_is_not_cached(self) -> None:
        """
        Тестируем: заготовка не должна задерживаться в кэше.
        Отдаём: два одинаковых вызова, где модель недоступна.
        Ожидаем: обращение к модели происходит каждый раз заново.
        """
        client = build_client("llm-cache-fallback")
        transport = _Transport(LLMCallResult(fallback_batch(), generated=False))
        client._request_cards = transport

        await generate(client)
        await generate(client)

        assert transport.calls == 2

    async def test_cache_hit_is_attributed_to_model(self) -> None:
        """
        Тестируем: источник результата при попадании в кэш.
        Отдаём: повтор запроса после успешной модельной генерации.
        Ожидаем: партия помечена целиком модельной, заготовок нет.
        """
        client = build_client("llm-cache-attribution")
        transport = _Transport(LLMCallResult(model_batch(), generated=True))
        client._request_cards = transport

        await generate(client)
        cached = await generate(client)

        assert cached.model_count == BATCH_SIZE
        assert cached.fallback_count == 0
        assert cached.is_all_from_model is True

    async def test_partial_batch_is_not_cached(self) -> None:
        """
        Тестируем: партию с доливкой заготовками.
        Отдаём: ответ модели на два черновика из пяти.
        Ожидаем: в кэш он не лёг, повтор обратится к модели снова.
        """
        partial = GeneratedCardBatchDTO(
            drafts=[draft("Тема одна"), draft("Тема две")],
            model_count=2,
            fallback_count=3,
        )
        client = build_client("llm-cache-partial")
        transport = _Transport(LLMCallResult(partial, generated=False))
        client._request_cards = transport

        await generate(client)
        await generate(client)

        assert transport.calls == 2

    async def test_different_batch_numbers_do_not_share_cache(self) -> None:
        """
        Тестируем: разделение кэша по номеру партии.
        Отдаём: генерацию партий 1 и 2.
        Ожидаем: обе дошли до модели, а номер партии реально различается в контексте.
        """
        client = build_client("llm-cache-batch-numbers")
        transport = _Transport(LLMCallResult(model_batch(), generated=True))
        client._request_cards = transport

        await generate(client, batch_number=1)
        await generate(client, batch_number=2)

        assert transport.calls == 2
        assert [payload["batch_number"] for payload in transport.payloads] == [1, 2]


class TestSingleFlight:
    """Группа тестов защиты от одновременной одинаковой генерации."""

    async def test_concurrent_identical_requests_hit_model_once(self) -> None:
        """
        Тестируем: два одновременных одинаковых запроса.
        Отдаём: параллельные вызовы, разблокированные после обоих стартов.
        Ожидаем: модель вызывается один раз, второй ждёт и берёт из кэша.
        """
        gate = asyncio.Event()
        client = build_client("llm-cache-single-flight")
        transport = _Transport(LLMCallResult(model_batch(), generated=True), gate=gate)
        client._request_cards = transport

        running = asyncio.gather(generate(client), generate(client))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        gate.set()
        first, second = await running

        assert transport.calls == 1
        assert len(first.drafts) == BATCH_SIZE
        assert len(second.drafts) == BATCH_SIZE
