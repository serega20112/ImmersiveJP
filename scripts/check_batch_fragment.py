"""Проверить, что HTML-фрагмент партии рендерится во всех состояниях генерации.

Фрагмент подменяет собой список карточек на странице трека каждые две секунды,
но тесты его не рендерят, а опечатка в имени поля DTO превращается в 500 только
у пользователя. Скрипт прогоняет все три состояния генерации через тот же
шаблонизатор, что и приложение.

Запуск:
    python -m scripts.check_batch_fragment
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.requests import Request

from src.application.dto.learning import (
    CardBatchStatusDTO,
    CardExampleDTO,
    KeyTermDTO,
    TrackCardDTO,
)
from src.main import create_app

TEMPLATE_NAME = "learn/partials/batch_cards.html"
EXPECTED_CARDS = 5


def build_request(app: FastAPI) -> Request:
    """Собрать минимальный запрос, чтобы url_for работал вне сервера.

    Args:
        app: Построенное приложение.

    Returns:
        Запрос с приложением в scope.
    """
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/learn/culture",
        "raw_path": b"/learn/culture",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")],
        "server": ("testserver", 80),
        "client": ("test", 1234),
        "app": app,
    }
    return Request(scope)


def build_card(position: int) -> TrackCardDTO:
    """Собрать карточку для фрагмента.

    Args:
        position: Позиция в партии.

    Returns:
        Карточка, заполненная минимально, но полем в поле.
    """
    return TrackCardDTO(
        id=position,
        track="culture",
        topic=f"Тема {position}",
        preview=f"Превью {position}",
        explanation=f"Объяснение {position}",
        examples=[
            CardExampleDTO(
                raw_text="例。 | rei. | Пример.",
                japanese="例。",
                romaji="rei.",
                translation="Пример.",
            )
        ],
        key_terms=["語"],
        key_term_items=[KeyTermDTO(raw_text="語", label="語", translation="слово")],
        batch_number=1,
        position=position,
        is_completed=position == 1,
    )


def build_status(state: str, written: int) -> CardBatchStatusDTO:
    """Собрать состояние партии.

    Args:
        state: Ключ состояния: ready, generating или failed.
        written: Сколько карточек уже записано.

    Returns:
        Статус партии для шаблона.
    """
    return CardBatchStatusDTO(
        state=state,
        is_generating=state == "generating",
        is_failed=state == "failed",
        batch_number=1,
        expected_cards=EXPECTED_CARDS,
        cards=[build_card(position) for position in range(1, written + 1)],
    )


def main() -> int:
    """Отрендерить фрагмент во всех состояниях и проверить содержимое.

    Returns:
        Код завершения: 0 — все состояния рендерятся, 1 — есть рассогласование.
    """
    app = create_app()
    request = build_request(app)
    templates = app.state.templates

    cases = {
        "generating": (build_status("generating", 2), ["data-batch-generating", "из 5"]),
        "failed": (build_status("failed", 1), ["оборвалась"]),
        "ready": (build_status("ready", EXPECTED_CARDS), ["Тема 5", "Пройдено"]),
    }
    failures: list[str] = []

    for state, (status, markers) in cases.items():
        html = templates.get_template(TEMPLATE_NAME).render(
            request=request,
            status=status,
            track="culture",
        )
        cards_found = html.count("preview-card__meta")
        expected_cards = len(status.cards)
        if cards_found != expected_cards:
            failures.append(
                f"{state}: карточек отрендерено {cards_found}, ожидалось {expected_cards}"
            )
        for marker in markers:
            if marker not in html:
                failures.append(f"{state}: в разметке нет маркера {marker!r}")
        print(f"{state:<11}: {len(html)} символов, карточек {cards_found}")

    if failures:
        for line in failures:
            print(f"FAIL {line}")
        print("RESULT: FRAGMENT MISMATCH")
        return 1

    print("RESULT: FRAGMENT RENDERS IN ALL STATES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
