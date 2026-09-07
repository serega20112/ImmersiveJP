"""DTO наставника: сообщения, фокусы обучения и страница наставника."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MentorMessageDTO(BaseModel):
    """Сообщение в диалоге с наставником.

    Атрибуты:
        role: Роль автора сообщения (``user`` или ``assistant``).
        content: Текст сообщения.
        created_at_label: Время создания в формате ``ЧЧ:ММ``.
        action_steps: Рекомендуемые шаги из сообщения наставника.
    """

    model_config = ConfigDict(frozen=True)

    role: str
    content: str
    created_at_label: str
    action_steps: list[str] = Field(default_factory=list)


class MentorFocusDTO(BaseModel):
    """Текущий фокус обучения, выставленный наставником.

    Атрибуты:
        key: Ключ фокуса (например, ``grammar``).
        title: Человекочитаемое название фокуса.
        note: Пояснение, на что делать упор.
        track: Трек, к которому относится фокус.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    title: str
    note: str
    track: str


class MentorReplyDTO(BaseModel):
    """Ответ наставника на сообщение пользователя.

    Атрибуты:
        reply: Текст ответа.
        action_steps: Рекомендуемые действия.
        suggested_prompts: Варианты продолжения диалога.
    """

    model_config = ConfigDict(frozen=True)

    reply: str
    action_steps: list[str] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)


class MentorPageDTO(BaseModel):
    """Страница наставника.

    Атрибуты:
        title: Заголовок страницы.
        subtitle: Подзаголовок страницы.
        next_step: Следующий рекомендуемый шаг.
        current_stage_title: Название текущего этапа плана.
        pace_title: Название текущего темпа.
        content_mode_title: Название текущего режима контента.
        active_focus: Текущий фокус обучения.
        messages: История переписки с наставником.
        suggested_prompts: Подсказки для продолжения диалога.
        draft_message: Черновик сообщения пользователя.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    next_step: str
    current_stage_title: str
    pace_title: str
    content_mode_title: str
    active_focus: MentorFocusDTO | None = None
    messages: list[MentorMessageDTO] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)
    draft_message: str = ""
