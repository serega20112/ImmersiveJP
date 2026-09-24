"""Разведка боем: один реальный запрос генерации карточек.

Тратит квоту провайдера. Нужен, чтобы решить, кто должен определять
принадлежность карточки треку: лексический фильтр в коде или сама модель.
Запрос строится через боевые _build_endpoints, _request_runtime и
_build_request_body, а ответ разбирается боевым _extract_json — иначе вывод
описывал бы мою аппроксимацию, а не продакшн.

Дополнительно к production-инструкции просит поле track у каждой карточки: по
нему видно, умеет ли модель сама маркировать материал без потери качества.

Использование (из корня репозитория):
    python -m scripts.probe_live_card_generation [track]
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any

import httpx

from src.domain.value_objects.track_type import TrackType
from src.infrastructures.external.llm.client import HuggingFaceLLMClient

PRODUCTION_SYSTEM_CONTENT = (
    "Ты методист по Японии. Верни только компактный JSON-массив без текста вне JSON. "
    "Ровно по одной карточке на каждый запрошенный элемент. "
    "Каждая карточка должна содержать topic, explanation, key_terms. "
    "examples: от 1 до 3 очень коротких строк либо пустой массив. "
    "explanation делай кратким и прикладным. key_terms: ровно 3 строки."
)

TRACK_FIELD_INSTRUCTION = (
    "Кроме того, у каждой карточки верни поле track: one из language, culture, history — "
    "треку какого типа принадлежит материал карточки."
)

BATCH_SIZE = 5


class MemoryStore:
    """Хранилище на словаре: клиенту нужны кулдаун и состояние предохранителя."""

    def __init__(self) -> None:
        """Инициализировать пустое хранилище."""
        self.data: dict[str, Any] = {}

    async def get_json(self, key: str) -> Any:
        """Вернуть сохранённое значение по ключу."""
        return self.data.get(key)

    async def set_json(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        """Сохранить значение; TTL в этом хранилище не ограничивается."""
        del expire_seconds
        self.data[key] = value

    async def delete(self, key: str) -> None:
        """Удалить ключ."""
        self.data.pop(key, None)

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Увеличить счётчик и вернуть новое значение."""
        del expire_seconds
        value = int(self.data.get(key) or 0) + 1
        self.data[key] = value
        return value

    async def close(self) -> None:
        """Закрыть соединение; нечего закрывать."""


def build_payload(track: TrackType) -> dict:
    """Собрать контекст генерации, близкий к реальному новичку.

    Args:
        track: Трек, для которого генерируется партия.

    Returns:
        Payload, совместимый с _build_cards_prompt и _request_runtime.
    """
    return {
        "kind": "cards",
        "user_id": 1,
        "track": track.value,
        "batch_number": 1,
        "batch_size": BATCH_SIZE,
        "goal": "tourism",
        "language_level": "zero",
        "study_timeline": "six_months",
        "interests": ["аниме", "путешествия", "готовить дома"],
        "previous_topics": [],
        "previous_key_terms": [],
        "diagnostic_level": "zero",
        "diagnostic_summary": "Быстрый тест: 2/5.",
        "strengths": [],
        "weak_points": ["Хирагана", "Частицы"],
        "mentor_focus": None,
    }


async def call(client: HuggingFaceLLMClient, payload: dict) -> tuple[object, dict]:
    """Выполнить один реальный запрос к первому доступному endpoint.

    Args:
        client: Боевой клиент LLM с хранилищем в памяти.
        payload: Контекст генерации.

    Returns:
        Кортеж разобранного ответа и метаданных вызова.

    Raises:
        RuntimeError: Если ни один endpoint не вернул ответ.
    """
    _, timeout_seconds, _, max_tokens = client._request_runtime(payload)
    endpoint = client._build_endpoints(payload)[0]
    body = client._build_request_body(
        endpoint=endpoint,
        payload=payload,
        temperature=0.35,
        system_content=PRODUCTION_SYSTEM_CONTENT + TRACK_FIELD_INSTRUCTION,
        user_content=client._build_cards_prompt(payload),
        max_tokens=max_tokens,
    )
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout_seconds) as http:
        response = await http.post(
            endpoint.url,
            headers={
                "Authorization": f"Bearer {endpoint.token}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    response.raise_for_status()
    raw = response.json()
    content = client._extract_response_content(raw)
    meta = {
        "provider": endpoint.provider,
        "model": endpoint.model,
        "max_tokens": max_tokens,
        "timeout_seconds": timeout_seconds,
        "elapsed_ms": elapsed_ms,
        "http_status": response.status_code,
        "finish_reason": (raw.get("choices") or [{}])[0].get("finish_reason"),
        "usage": raw.get("usage"),
        "content_length": len(content),
    }
    return client._extract_json(content), meta


def report(parsed: object, meta: dict, track: TrackType) -> None:
    """Напечатать разбор ответа модели и вердикт лексического фильтра.

    Args:
        parsed: Разобранный JSON-ответ.
        meta: Метаданные HTTP-вызова.
        track: Трек, для которого просили партию.
    """
    print("=== вызов ===")
    printable = {key: value for key, value in meta.items() if key != "token"}
    print(json.dumps(printable, ensure_ascii=False, indent=2, default=str))

    items = parsed if isinstance(parsed, list) else []
    print(f"\n=== карточек в ответе: {len(items)} (запрошено {BATCH_SIZE}) ===")

    declared_ok = 0
    filter_ok = 0
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            print(f"{index}. НЕ-ОБЪЕКТ: {str(item)[:80]}")
            continue
        topic = str(item.get("topic") or "").strip()
        explanation = str(item.get("explanation") or "").strip()
        declared = str(item.get("track") or "").strip().lower()
        key_terms = HuggingFaceLLMClient._normalize_key_terms(
            item.get("key_terms") or [], track=track.value
        )
        examples = HuggingFaceLLMClient._normalize_card_examples(item.get("examples") or [])
        matches = HuggingFaceLLMClient._card_matches_track(
            track=track.value,
            topic=topic,
            explanation=explanation,
            examples=examples,
            key_terms=key_terms,
        )
        declared_ok += int(declared == track.value)
        filter_ok += int(matches)
        print(f"\n{index}. {topic}")
        print(
            f"   объявленный трек : {declared or 'ОТСУТСТВУЕТ'}  {'OK' if declared == track.value else 'РАСХОЖДЕНИЕ'}"
        )
        print(f"   примеров          : {len(examples)}")
        print(f"   key_terms         : {len(key_terms)}")
        print(f"   лекс. фильтр      : {'пропустил' if matches else 'ОТКЛОНИЛ'}")
        print(f"   explanation       : {explanation[:150]}")

    print("\n=== итог ===")
    print(f"  модель сама пометила трек верно : {declared_ok} из {len(items)}")
    print(f"  лексический фильтр пропустил    : {filter_ok} из {len(items)}")


async def main() -> None:
    """Выполнить один живой запрос и показать разбор."""
    track_value = sys.argv[1] if len(sys.argv) > 1 else TrackType.CULTURE.value
    track = TrackType(track_value)
    payload = build_payload(track)
    client = HuggingFaceLLMClient(MemoryStore())
    print(f"трек={track.value}; выполняется ОДИН реальный запрос к провайдеру.\n")
    parsed, meta = await call(client, payload)
    report(parsed, meta, track)


if __name__ == "__main__":
    asyncio.run(main())
