"""
Юнит-тесты DTO наставника.

Проверяются: значения по умолчанию сообщений и страницы,
а также вложенность текущего фокуса обучения.
"""

from src.application.dto.mentor import (
    MentorFocusDTO,
    MentorMessageDTO,
    MentorPageDTO,
    MentorReplyDTO,
)


class TestMentorMessageDTO:
    """Группа тестов DTO сообщения в диалоге с наставником."""

    def test_action_steps_default_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию списка рекомендуемых шагов.
        Отдаём: сообщение без шагов.
        Ожидаем: action_steps — пустой список.
        """
        dto = MentorMessageDTO(role="user", content="Привет", created_at_label="10:00")

        assert dto.action_steps == []


class TestMentorReplyDTO:
    """Группа тестов DTO ответа наставника."""

    def test_optional_lists_default_to_empty(self) -> None:
        """
        Тестируем: значения по умолчанию шагов и подсказок.
        Отдаём: ответ только с текстом.
        Ожидаем: action_steps и suggested_prompts — пустые списки.
        """
        dto = MentorReplyDTO(reply="Продолжай")

        assert dto.action_steps == []
        assert dto.suggested_prompts == []


class TestMentorPageDTO:
    """Группа тестов DTO страницы наставника."""

    def _page(self, **overrides: object) -> MentorPageDTO:
        payload = {
            "title": "Наставник",
            "subtitle": "Подзаголовок",
            "next_step": "Шаг",
            "current_stage_title": "Этап",
            "pace_title": "Темп",
            "content_mode_title": "Режим",
        }
        payload.update(overrides)
        return MentorPageDTO(**payload)

    def test_defaults_for_optional_parts(self) -> None:
        """
        Тестируем: значения по умолчанию необязательных частей страницы.
        Отдаём: только обязательные текстовые поля.
        Ожидаем: фокус None, списки пусты, черновик — пустая строка.
        """
        page = self._page()

        assert page.active_focus is None
        assert page.messages == []
        assert page.suggested_prompts == []
        assert page.draft_message == ""

    def test_nests_active_focus(self) -> None:
        """
        Тестируем: вложенность текущего фокуса обучения.
        Отдаём: фокус грамматики.
        Ожидаем: фокус доступен через поле страницы.
        """
        focus = MentorFocusDTO(key="grammar", title="Грамматика", note="Упор", track="jlpt")

        page = self._page(active_focus=focus)

        assert page.active_focus is not None
        assert page.active_focus.key == "grammar"
