"""
Юнит-тесты сервисов-фасадов дашборда и проверки знаний.

Оба сервиса не содержат собственной логики: они делегируют работу
use case-объектам, поэтому проверяется точность передачи аргументов.
"""

from __future__ import annotations

import pytest

from src.application.dto.knowledge import KnowledgeCheckPageDTO, KnowledgeQuestionDTO
from src.application.dto.profile import DashboardDTO
from src.application.services import DashboardService, KnowledgeService
from tests.fixtures.factories.progress_factory import build_trust_score
from tests.fixtures.fakes import StubUseCase


def _dashboard() -> DashboardDTO:
    """Собрать корректный DTO дашборда для ответа-заглушки."""
    return DashboardDTO(
        user_display_name="Ая",
        recommendation="Продолжай",
        sections=[],
        trust_score=build_trust_score(),
        speech_practice_href="/learn/speech",
    )


def _knowledge_page(**overrides: object) -> KnowledgeCheckPageDTO:
    """Собрать корректный DTO страницы проверки знаний."""
    payload = {
        "title": "Проверка",
        "subtitle": "Подзаголовок",
        "focus_area": "",
    }
    payload.update(overrides)
    return KnowledgeCheckPageDTO(**payload)


class TestDashboardService:
    """Группа тестов сервиса дашборда."""

    async def test_forwards_user_id(self) -> None:
        """
        Тестируем: делегирование получения дашборда.
        Отдаём: идентификатор пользователя.
        Ожидаем: use case получил его, сервис вернул тот же объект.
        """
        use_case = StubUseCase(_dashboard())

        result = await DashboardService(get_dashboard_use_case=use_case).get_dashboard(7)

        assert use_case.calls == [(7,)]
        assert result is use_case.result


class TestKnowledgeService:
    """Группа тестов сервиса проверки знаний."""

    def _service(self, generate: StubUseCase, submit: StubUseCase) -> KnowledgeService:
        return KnowledgeService(
            generate_knowledge_check_use_case=generate,
            submit_knowledge_check_use_case=submit,
        )

    async def test_generate_check_forwards_focus_area(self) -> None:
        """
        Тестируем: делегирование генерации проверки знаний.
        Отдаём: идентификатор пользователя и область фокуса.
        Ожидаем: use case получил оба аргумента, результат возвращён.
        """
        page = _knowledge_page(focus_area="грамматика")
        generate = StubUseCase(page)

        result = await self._service(generate, StubUseCase(None)).generate_check(3, "грамматика")

        assert generate.calls == [(3, "грамматика")]
        assert result is page

    async def test_generate_check_uses_empty_focus_by_default(self) -> None:
        """
        Тестируем: значение области фокуса по умолчанию.
        Отдаём: только идентификатор пользователя.
        Ожидаем: use case получил пустую строку как область фокуса.
        """
        generate = StubUseCase(_knowledge_page())

        await self._service(generate, StubUseCase(None)).generate_check(3)

        assert generate.calls == [(3, "")]

    async def test_submit_check_forwards_questions_and_answers(self) -> None:
        """
        Тестируем: делегирование проверки ответов.
        Отдаём: список вопросов и карту ответов.
        Ожидаем: use case получил те же объекты, результат возвращён.
        """
        questions = [KnowledgeQuestionDTO(id="q1", kind="translate", question="Вопрос")]
        page = _knowledge_page(questions=questions)
        submit = StubUseCase(page)

        result = await self._service(StubUseCase(None), submit).submit_check(questions, {"q1": "a"})

        assert submit.calls == [(questions, {"q1": "a"})]
        assert result is page
