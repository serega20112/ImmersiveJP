"""
Юнит-тесты сборки кандидатов и ротации токенов.

Проверяется поведение, которое до этого подтверждалось только живыми запросами к
провайдерам: каждый токен из CSV-списка обязан стать отдельным кандидатом,
исчерпанный баланс должен уводить к следующему ключу, а ошибка в форме запроса —
не сжигать следующий ключ впустую.
"""

from __future__ import annotations

import httpx
import pytest

from src.config.settings import settings
from src.infrastructures.cache import KeyValueStore
from src.infrastructures.external.llm.client import HuggingFaceLLMClient
from src.infrastructures.external.llm.requests import _Endpoint

CARDS_PAYLOAD = {"kind": "cards", "track": "culture", "batch_number": 1, "batch_size": 5}


def status_error(status_code: int) -> httpx.HTTPStatusError:
    """Собрать ошибку HTTP-ответа с указанным статусом.

    Args:
        status_code: Код статуса ответа.

    Returns:
        Исключение httpx с готовым response.
    """
    request = httpx.Request("POST", "https://router.example.test/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("provider answered", request=request, response=response)


def endpoint_for(token: str, provider: str = "huggingface") -> _Endpoint:
    """Собрать кандидата обращения с указанным токеном.

    Args:
        token: Значение ключа доступа.
        provider: Имя провайдера.

    Returns:
        Кандидат обращения.
    """
    return _Endpoint(
        provider=provider,
        url="https://router.example.test/v1/chat/completions",
        token=token,
        model="test/model-a",
    )


def build_client(namespace: str) -> HuggingFaceLLMClient:
    """Собрать клиента на in-memory хранилище.

    Args:
        namespace: Namespace хранилища, изолирующий тесты друг от друга.

    Returns:
        Клиент генерации.
    """
    return HuggingFaceLLMClient(KeyValueStore(redis_url=None, namespace=namespace))


@pytest.fixture
def provider_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Установить детерминированные настройки провайдеров.

    Значения берутся не из .env: тест на ротацию, зависящий от реальных ключей,
    либо молчал бы без ключей, либо сжигал баланс.
    """
    values = {
        "hf_api_token": " hf-one , hf-two ,, hf-three ",
        "hf_api_url": "https://router.huggingface.co/v1/chat/completions",
        "hf_model": "test/model-a",
        "hf_cards_model": "",
        "hf_provider": "",
        "openrouter_api_key": "or-one,or-two",
        "openrouter_api_url": "https://openrouter.ai/api/v1/chat/completions",
        "openrouter_model": "test/model-b",
    }
    for name, value in values.items():
        monkeypatch.setattr(settings.llm, name, value)


class TestEndpointBuilding:
    """Группа тестов списка кандидатов обращения."""

    @pytest.mark.usefixtures("provider_settings")
    def test_every_hf_token_becomes_its_own_candidate(self) -> None:
        """
        Тестируем: разбор CSV-списка ключей Hugging Face.
        Отдаём: три токена с пробелами и пустым элементом между запятыми.
        Ожидаем: три кандидата, токены очищены, пустых нет.
        """
        client = build_client("llm-endpoints-hf")

        endpoints = client._build_endpoints(CARDS_PAYLOAD)

        hf_tokens = [item.token for item in endpoints if item.provider == "huggingface"]
        assert hf_tokens == ["hf-one", "hf-two", "hf-three"]

    @pytest.mark.usefixtures("provider_settings")
    def test_huggingface_candidates_come_before_openrouter(self) -> None:
        """
        Тестируем: порядок кандидатов.
        Отдаём: настроенный основной провайдер и резерв.
        Ожидаем: сначала все ключи Hugging Face, затем все ключи OpenRouter.
        """
        client = build_client("llm-endpoints-order")

        providers = [item.provider for item in client._build_endpoints(CARDS_PAYLOAD)]

        assert providers == [
            "huggingface",
            "huggingface",
            "huggingface",
            "openrouter",
            "openrouter",
        ]

    @pytest.mark.usefixtures("provider_settings")
    def test_openrouter_needs_key_and_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Тестируем: половинчатую настройку резерва.
        Отдаём: ключи OpenRouter при пустой модели.
        Ожидаем: резерв не участвует, вместо провального обращения к нему.
        """
        client = build_client("llm-endpoints-or-no-model")
        monkeypatch.setattr(settings.llm, "openrouter_model", "")

        providers = {item.provider for item in client._build_endpoints(CARDS_PAYLOAD)}

        assert providers == {"huggingface"}

    @pytest.mark.usefixtures("provider_settings")
    def test_excluded_provider_is_dropped_entirely(self) -> None:
        """
        Тестируем: исключение провайдера по открытому предохранителю.
        Отдаём: запрос с исключённым huggingface.
        Ожидаем: остались только кандидаты OpenRouter.
        """
        client = build_client("llm-endpoints-exclude")

        endpoints = client._build_endpoints(CARDS_PAYLOAD, exclude_providers={"huggingface"})

        assert {item.provider for item in endpoints} == {"openrouter"}

    def test_no_credentials_yields_no_candidates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Тестируем: отсутствие ключей вообще.
        Отдаём: пустые hf_api_token и openrouter_api_key.
        Ожидаем: кандидатов нет — генерация уходит в заготовку, а не в слепой запрос.
        """
        monkeypatch.setattr(settings.llm, "hf_api_token", "")
        monkeypatch.setattr(settings.llm, "openrouter_api_key", "")
        client = build_client("llm-endpoints-empty")

        assert client._build_endpoints(CARDS_PAYLOAD) == []


class TestFailureClassification:
    """Группа тестов отображения кода ответа в причину отказа."""

    @pytest.mark.parametrize(
        ("status_code", "expected_reason"),
        [
            (401, "auth_failed"),
            (402, "payment_required"),
            (403, "permission_denied"),
            (404, "model_not_available"),
            (410, "model_no_longer_supported"),
            (422, "invalid_request"),
            (429, "rate_limited"),
            (503, "provider_http_503"),
        ],
    )
    def test_http_statuses(self, status_code: int, expected_reason: str) -> None:
        """
        Тестируем: классификацию ответа провайдера по коду статуса.
        Отдаём: ошибку HTTP с указанным кодом.
        Ожидаем: ожидаемое значение причины.
        """
        reason = HuggingFaceLLMClient._fallback_reason_from_error(status_error(status_code))

        assert reason == expected_reason

    def test_transport_and_timeout(self) -> None:
        """
        Тестируем: сетевые отказы без кода ответа.
        Отдаём: таймаут соединения и ошибку чтения.
        Ожидаем: timeout и transport_error соответственно.
        """
        timeout = httpx.ConnectTimeout("slow")
        transport = httpx.ReadError("closed")

        assert HuggingFaceLLMClient._fallback_reason_from_error(timeout) == "timeout"
        assert HuggingFaceLLMClient._fallback_reason_from_error(transport) == "transport_error"


class TestFailoverDecisions:
    """Группа тестов решения идти ли на следующий ключ."""

    @pytest.mark.parametrize(
        ("reason", "should_failover"),
        [
            ("payment_required", True),
            ("model_no_longer_supported", True),
            ("rate_limited", True),
            ("auth_failed", True),
            ("timeout", True),
            ("transport_error", True),
            ("provider_http_503", True),
            ("invalid_request", False),
            ("http_400", False),
            ("unknown", False),
        ],
    )
    def test_which_reasons_move_to_next_credential(
        self, reason: str, should_failover: bool
    ) -> None:
        """
        Тестируем: набор причин, при которых стоит брать следующий ключ.
        Отдаём: причину отказа.
        Ожидаем: исчерпанный баланс и недоступность уводят дальше, а некорректный
            запрос — нет: новым ключом он не починится и лишь сожжёт баланс зря.
        """
        assert HuggingFaceLLMClient._is_failover_reason(reason) is should_failover


class TestTokenCooldown:
    """Группа тестов персонального кулдауна ключа."""

    def test_cooldown_key_does_not_leak_the_token(self) -> None:
        """
        Тестируем: формирование ключа кулдауна.
        Отдаём: кандидата с секретным токеном.
        Ожидаем: токен в ключ не попадает, вместо него хеш.
        """
        client = build_client("llm-cooldown-key")
        endpoint = endpoint_for("super-secret-token")

        key = client._token_cooldown_key(endpoint)

        assert "super-secret-token" not in key
        assert key.startswith("llm:token_cooldown:huggingface:")

    def test_distinct_tokens_get_distinct_cooldown_keys(self) -> None:
        """
        Тестируем: различимость ключей кулдауна разных токенов.
        Отдаём: двух кандидатов одного провайдера с разными токенами.
        Ожидаем: ключи различаются, иначе блокировка одного глушила бы всех.
        """
        client = build_client("llm-cooldown-distinct")

        first = client._token_cooldown_key(endpoint_for("token-first"))
        second = client._token_cooldown_key(endpoint_for("token-second"))

        assert first != second

    async def test_cooling_one_token_leaves_others_usable(self) -> None:
        """
        Тестируем: изоляцию кулдауна между ключами одного провайдера.
        Отдаём: два ключа и отказ по первому.
        Ожидаем: первый заблокирован, второй по-прежнему доступен.
        """
        client = build_client("llm-cooldown-isolation")
        first = endpoint_for("token-first")
        second = endpoint_for("token-second")

        await client._set_endpoint_cooldown(first, reason="payment_required")

        assert await client._is_endpoint_cooled_down(first) is True
        assert await client._is_endpoint_cooled_down(second) is False
