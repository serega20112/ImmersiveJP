"""Разведка формы ответа совета: что возвращает модель и помогает ли response_format.

Три платных запроса. Совет не починился ужесточением промпта, поэтому нужно
фактами решить, каким способом получать объект: обязательем формата от провайдера
или разбором того, что модель всё равно отдаёт.

Использование (из корня репозитория):
    python -m scripts.probe_advice_response_shape [user_id]
"""

from __future__ import annotations

import asyncio
import sys

import httpx

from src.application.use_cases.profile.build_progress_report import BuildProgressReportUseCase
from src.config.settings import settings
from src.infrastructures.cache import KeyValueStore
from src.infrastructures.database import database as db_module
from src.infrastructures.external.llm.client import HuggingFaceLLMClient
from src.infrastructures.repositories.database import ImmersiveUnitOfWork

ADVICE_SYSTEM_CONTENT = (
    "Ты редактор учебных рекомендаций ImmersJP. "
    'Верни строго один JSON-объект вида {"headline": "...", "summary": "...", '
    '"focus_points": ["...", "...", "..."]}. '
    "Массив строк вместо объекта не принимается. "
    "Тон спокойный, короткий, практический. Без markdown и текста вне JSON."
)


def build_client() -> HuggingFaceLLMClient:
    """Собрать клиента так же, как это делает DI-контейнер.

    Returns:
        Боевой клиент LLM поверх реального хранилища.
    """
    store = KeyValueStore(
        redis_url=settings.redis.redis_url if settings.redis.redis_enabled else None,
        namespace="immersjp",
        required=settings.redis.redis_required,
    )
    return HuggingFaceLLMClient(store)


async def call(client: HuggingFaceLLMClient, body: dict, label: str) -> None:
    """Перебрать endpoint'ы, как боевой цикл, и показать форму ответа.

    Первый токен может быть исчерпан, а _request_llm_json в проде идёт по всем
    кандидатам. Зонд обязан делать то же самое, иначе он меряет не модель,
    а баланс одного конкретного токена.

    Args:
        client: Боевой клиент генерации.
        body: Тело запроса к endpoint.
        label: Подпись варианта для вывода.
    """
    endpoints = client._build_endpoints({"kind": "advice"})
    last_problem = "не было ни одной попытки"
    for index, endpoint in enumerate(endpoints, start=1):
        async with httpx.AsyncClient(timeout=40) as http:
            try:
                response = await http.post(
                    endpoint.url,
                    headers={
                        "Authorization": f"Bearer {endpoint.token}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
            except Exception as error:
                last_problem = f"сбой сети {type(error).__name__}"
                continue

        if response.status_code != 200:
            last_problem = f"HTTP {response.status_code}: {response.text[:170]}"
            print(f"{label}: токен {index} -> HTTP {response.status_code}")
            continue

        content = client._extract_response_content(response.json())
        print(f"{label}: токен {index} -> HTTP 200")
        print("   сырой ответ     :", content[:300].replace("\n", " "))
        try:
            parsed = client._extract_json(content)
        except Exception as error:
            print("   парсер не справился:", type(error).__name__)
            return
        print("   тип разобранного:", type(parsed).__name__)
        if isinstance(parsed, list):
            print("   элементов в массиве:", len(parsed))
        else:
            print("   ключи объекта    :", sorted(parsed))
        return

    print(
        f"{label}: все токены исчерпаны; последняя проблема ->",
        last_problem.replace("\n", " ")[:200],
    )


async def main() -> None:
    """Сравнить обычный запрос и запрос с обязательным JSON-объектом."""
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    client = build_client()
    try:
        uow = ImmersiveUnitOfWork(db_module.get_session_factory())
        async with uow as session_uow:
            user = await session_uow.repository("user").get_by_id(user_id)
        if user is None:
            raise SystemExit(f"Пользователь {user_id} не найден")
        report = await BuildProgressReportUseCase(uow).execute(user_id)
        payload = {"kind": "advice", "user_id": user_id}
        model, _, _, max_tokens = client._request_runtime(payload)
        user_content = client._build_advice_prompt(user, report)

        base = {
            "model": model,
            "temperature": 0.6,
            "max_tokens": max_tokens,
            "reasoning_effort": "low",
            "messages": [
                {"role": "system", "content": ADVICE_SYSTEM_CONTENT},
                {"role": "user", "content": user_content},
            ],
        }
        print("модель:", model, "| max_tokens:", max_tokens)
        print("\n=== A: как сейчас ===")
        await call(client, dict(base), "A")
        print("\n=== B: response_format=json_object ===")
        forced = dict(base)
        forced["response_format"] = {"type": "json_object"}
        await call(client, forced, "B")
        print("\n=== C: один пример-каркас прямо в user-контенте ===")
        framed = dict(base)
        framed["messages"] = [
            {"role": "system", "content": ADVICE_SYSTEM_CONTENT},
            {
                "role": "user",
                "content": user_content
                + '\nОтвет начни со слова headline внутри фигурных скобок: {"headline": ...',
            },
        ]
        await call(client, framed, "C")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
