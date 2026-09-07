"""Доменные алгоритмы разбиения текста и векторного сравнения."""

from __future__ import annotations

from math import sqrt

from src.domain.entities.document_chunk import DocumentChunk


def chunk_documents(
    documents: list,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """Разбить документы на перекрывающиеся фрагменты.

    Args:
        documents: Документы с атрибутами id и content.
        chunk_size: Размер фрагмента в символах.
        chunk_overlap: Размер перекрытия соседних фрагментов.

    Returns:
        Список фрагментов с привязкой к документам.
    """
    overlap = max(min(chunk_overlap, chunk_size - 1), 0)
    step = chunk_size - overlap
    chunks: list[DocumentChunk] = []
    for document in documents:
        text = " ".join(str(document.content or "").split())
        for start in range(0, len(text), step):
            chunk = text[start : start + chunk_size]
            if len(chunk) < overlap + 1 and chunks and chunks[-1].document_id == document.id:
                continue
            chunks.append(DocumentChunk(document_id=document.id, text=chunk))
    return chunks


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Вычислить косинусную близость двух векторов.

    Args:
        a: Первый вектор.
        b: Второй вектор.

    Returns:
        Косинусная близость; ноль для пустых или несовместимых векторов.
    """
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(ai * bi for ai, bi in zip(a, b, strict=True))
    norm_a = sqrt(sum(ai * ai for ai in a))
    norm_b = sqrt(sum(bi * bi for bi in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
