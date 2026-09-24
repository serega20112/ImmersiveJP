"""
Юнит-тесты DTO PDF-документа.

Проверяются: обязательность имени файла и содержимого,
значение по умолчанию MIME-типа и неизменяемость модели.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.learning.documents import PdfDocumentDTO


class TestPdfDocumentDTO:
    """Группа тестов DTO готового PDF-документа."""

    def test_media_type_defaults_to_pdf(self) -> None:
        """
        Тестируем: значение по умолчанию MIME-типа.
        Отдаём: документ без явного media_type.
        Ожидаем: media_type равен application/pdf.
        """
        dto = PdfDocumentDTO(filename="cards.pdf", content=b"%PDF-1.4")

        assert dto.media_type == "application/pdf"

    def test_keeps_binary_content(self) -> None:
        """
        Тестируем: сохранение бинарного содержимого.
        Отдаём: байты PDF-файла.
        Ожидаем: содержимое доступно без изменений.
        """
        dto = PdfDocumentDTO(filename="cards.pdf", content=b"\x00\x01")

        assert dto.content == b"\x00\x01"

    def test_is_frozen(self) -> None:
        """
        Тестируем: неизменяемость DTO документа.
        Отдаём: созданный DTO и попытку изменить имя файла.
        Ожидаем: ValidationError на присваивании.
        """
        dto = PdfDocumentDTO(filename="cards.pdf", content=b"x")

        with pytest.raises(ValidationError):
            dto.filename = "other.pdf"  # type: ignore[misc]
