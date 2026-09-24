"""Юнит-тесты менторских сущностей: MentorMessage и MentorFocus."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.mentor import MentorFocus, MentorMessage


class TestMentorEntities:
    """Группа тестов сообщений и фокусов ментора."""

    def test_mentor_message_is_frozen(self) -> None:
        """
        Тестируем: неизменяемость сообщения ментора.
        Отдаём: валидное сообщение.
        Ожидаем: попытка присвоить поле вызывает FrozenInstanceError.
        """
        message = MentorMessage(
            role="mentor",
            content="Ответ",
            created_at=datetime.now(UTC),
        )

        with pytest.raises(Exception, match=r"cannot assign to field|frozen"):
            message.content = "Другое"

    def test_mentor_focus_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию фокуса ментора.
        Отдаём: фокус без явного трека.
        Ожидаем: трек по умолчанию "language".
        """
        focus = MentorFocus(key="k", title="Заголовок", note="Заметка")

        assert focus.track == "language"
