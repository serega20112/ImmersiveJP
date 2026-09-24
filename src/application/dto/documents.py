"""DTO пользовательских конспектов."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserDocumentDTO(BaseModel):
    """Один пользовательский конспект в списке.

    Полного текста здесь намеренно нет: страница показывает список, и тащить
    целиком весь материал ради превью означало бы отдавать наружу лишнее.
    Страница одного конспекта — отдельная задача и отдельное DTO.

    Атрибуты:
        id: Идентификатор документа.
        title: Заголовок.
        preview: Начало текста для различения документов между собой.
        created_at: Дата создания в формате ISO.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    title: str
    preview: str
    created_at: str


class UserDocumentsPageDTO(BaseModel):
    """Страница списка пользовательских конспектов.

    Атрибуты:
        documents: Конспекты пользователя.
        character_count: Суммарный объём текста в символах.
    """

    model_config = ConfigDict(frozen=True)

    documents: list[UserDocumentDTO] = Field(default_factory=list)
    character_count: int = 0
