"""Юнит-тесты flash-сообщений в сессии (utils/flash)."""

from fastapi import Request

from src.presentation.http.utils.flash import flash, pop_flashes


def _request_with_session() -> Request:
    """Собрать Request с пустой сессией.

    Returns:
        Объект Request с scope-сессией.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "session": {},
    }
    return Request(scope)


class TestFlashMessages:
    """Группа тестов flash-очереди в сессии."""

    def test_flash_appends_message_with_category(self) -> None:
        """
        Тестируем: добавление сообщения в сессию.
        Отдаём: два сообщения разных категорий.
        Ожидаем: обе записи в очереди сессии в порядке добавления.
        """
        request = _request_with_session()

        flash(request, "Готово", "success")
        flash(request, "Ошибка", "error")

        queue = request.session["flash_messages"]
        assert queue == [
            {"message": "Готово", "category": "success"},
            {"message": "Ошибка", "category": "error"},
        ]

    def test_pop_flashes_clears_queue(self) -> None:
        """
        Тестируем: извлечение и очистку очереди.
        Отдаём: сессия с двумя сообщениями; затем повторный pop.
        Ожидаем: первый pop возвращает оба сообщения, второй — пустой список.
        """
        request = _request_with_session()
        flash(request, "Первое")
        flash(request, "Второе", "error")

        first = pop_flashes(request)
        second = pop_flashes(request)

        assert first == [
            {"message": "Первое", "category": "info"},
            {"message": "Второе", "category": "error"},
        ]
        assert second == []
        assert request.session["flash_messages"] == []
