"""DTO документов: экспорт в PDF."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PdfDocumentDTO(BaseModel):
    """PDF-документ, готовый для скачивания.

    Атрибуты:
        filename: Имя файла для скачивания.
        content: Бинарное содержимое документа.
        media_type: MIME-тип документа.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    filename: str
    content: bytes
    media_type: str = "application/pdf"
