"""Юнит-тесты сущности DocumentChunk: фрагмент для векторного поиска."""

from src.domain.entities.document_chunk import DocumentChunk


class TestDocumentChunk:
    """Группа тестов фрагмента документа."""

    def test_holds_document_link_and_text(self) -> None:
        """
        Тестируем: структуру фрагмента для векторного поиска.
        Отдаём: document_id и текст фрагмента.
        Ожидаем: значения сохранены как есть.
        """
        chunk = DocumentChunk(document_id=5, text="фрагмент")

        assert chunk.document_id == 5
        assert chunk.text == "фрагмент"
