from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PdfDocumentDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    filename: str
    content: bytes
    media_type: str = "application/pdf"
