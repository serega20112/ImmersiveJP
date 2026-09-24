"""Живая проверка боевого пути генерации: карточки и совет.

Два платных запроса к модели. Нужен, чтобы проверить не отдельный разбор
ответа, а сквозной путь с реальным пользователем, Redis-кэшем и
предохранителем: доедет ли партия целиком и вернёт ли модель объект после
ужесточения промпта.

Использование (из корня репозитория):
    python -m scripts.check_live_generation_paths [user_id]
"""

from __future__ import annotations

import asyncio
import sys

from src.application.dto.profile import ProgressReportDTO
from src.application.use_cases.profile.build_progress_report import BuildProgressReportUseCase
from src.config.settings import settings
from src.domain.aggregates.user import User
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.cache import KeyValueStore
from src.infrastructures.database import database as db_module
from src.infrastructures.external.llm.client import HuggingFaceLLMClient
from src.infrastructures.repositories.database import ImmersiveUnitOfWork

PROBE_BATCH_NUMBER = 900


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


async def probe_cards(client: HuggingFaceLLMClient, user: User) -> None:
    """Запросить партию карточек и показать, что в ней пришло от модели.

    Args:
        client: Боевой клиент генерации.
        user: Доменный пользователь.
    """
    drafts = await client.generate_cards(user, TrackType.LANGUAGE, PROBE_BATCH_NUMBER, 5, [])
    print(f"  карточек в партии : {len(drafts)}")
    for draft in drafts:
        print(f"    - {draft.topic[:56]:56} примеров={len(draft.examples)}")


async def probe_advice(
    client: HuggingFaceLLMClient,
    user: User,
    report: ProgressReportDTO,
) -> None:
    """Запросить совет и определить источник результата.

    Сравнение с заготовкой даёт ответ без гадания по тексту: модель ответила
    объектом или нормализатор ушёл в фолбэк.

    Args:
        client: Боевой клиент генерации.
        user: Доменный пользователь.
        report: Отчёт о прогрессе.
    """
    advice = await client.generate_advice(user, report)
    is_fallback = advice == client._fallback_advice(user, report)
    print(f"  headline          : {advice.headline}")
    print(f"  summary           : {advice.summary[:80]}")
    print(f"  focus_points      : {len(advice.focus_points)}")
    print("  источник          :", "ЗАГОТОВКА" if is_fallback else "МОДЕЛЬ")


async def main() -> None:
    """Выполнить оба живых вызова для одного пользователя."""
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    client = build_client()
    try:
        uow = ImmersiveUnitOfWork(db_module.get_session_factory())
        async with uow as session_uow:
            user = await session_uow.repository("user").get_by_id(user_id)
        if user is None:
            raise SystemExit(f"Пользователь {user_id} не найден")
        report = await BuildProgressReportUseCase(uow).execute(user_id)

        print(f"=== карточки language, пользователь {user_id} ===")
        await probe_cards(client, user)
        print(f"\n=== совет, пользователь {user_id} ===")
        await probe_advice(client, user, report)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
