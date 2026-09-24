"""
Юнит-тесты доменных алгоритмов text_search.

Проверяются разбиение документов на перекрывающиеся фрагменты и
вычисление косинусной близости векторов.
"""

import pytest

from src.domain.services.text_search import chunk_documents, cosine_similarity


class _Document:
    """Заглушка документа с атрибутами id и content для тестов."""

    def __init__(self, document_id: int | None, content: str) -> None:
        """Инициализировать заглушку документа.

        Args:
            document_id: Идентификатор документа.
            content: Текст документа.
        """
        self.id = document_id
        self.content = content


class TestChunkDocuments:
    """Группа тестов разбиения документов на фрагменты."""

    def test_splits_text_with_overlap(self) -> None:
        """
        Тестируем: перекрывающееся разбиение текста.
        Отдаём: документ из 20 символов, chunk_size=10, overlap=5.
        Ожидаем: несколько фрагментов; начало второго совпадает с концом первого.
        """
        document = _Document(1, "abcdefghijklmnopqrstuvwxyz")

        chunks = chunk_documents([document], chunk_size=10, chunk_overlap=5)

        assert len(chunks) > 1
        assert chunks[0].text == "abcdefghij"
        assert chunks[1].text.startswith(chunks[0].text[5:])

    def test_chunks_keep_document_id_and_normalized_text(self) -> None:
        """
        Тестируем: привязку фрагментов к документу и нормализацию пробелов.
        Отдаём: документ с переносами строк и id=7.
        Ожидаем: document_id сохранён; текст одинарными пробелами.
        """
        document = _Document(7, "строка1\n\nстрока2\n   строка3")

        chunks = chunk_documents([document], chunk_size=100, chunk_overlap=10)

        assert chunks[0].document_id == 7
        assert chunks[0].text == "строка1 строка2 строка3"

    def test_empty_documents_produce_no_chunks(self) -> None:
        """
        Тестируем: разбиение пустой коллекции.
        Отдаём: пустой список документов.
        Ожидаем: пустой список фрагментов.
        """
        assert chunk_documents([], chunk_size=10, chunk_overlap=2) == []


class TestCosineSimilarity:
    """Группа тестов косинусной близости."""

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            ([1.0, 0.0], [1.0, 0.0], 1.0),
            ([1.0, 0.0], [0.0, 1.0], 0.0),
            ([1.0, 0.0], [-1.0, 0.0], -1.0),
            ([], [], 0.0),
            ([1.0], [1.0, 2.0], 0.0),
            ([0.0, 0.0], [1.0, 1.0], 0.0),
        ],
        ids=["same", "orthogonal", "opposite", "empty", "length-mismatch", "zero-vector"],
    )
    def test_similarity_cases(self, a: list[float], b: list[float], expected: float) -> None:
        """
        Тестируем: косинусную близость на граничных случаях.
        Отдаём: одинаковые, ортогональные, противоположные, пустые и
                несовместимые векторы.
        Ожидаем: 1.0, 0.0, -1.0 и ноль для вырожденных случаев.
        """
        assert cosine_similarity(a, b) == pytest.approx(expected)
