import os
from typing import List

from src.backend.infrastructure.external.embedding_client import EmbeddingClient
from src.backend.infrastructure.repositories.user_document_repository import UserDocumentRepository
from src.backend.infrastructure.models.user_document_model import UserDocument

import faiss
import numpy as np

class RAGService:
    """Service that builds a FAISS index over a user's documents and retrieves relevant chunks.

    The index is kept in memory per process. For production you would persist it,
    but for the scope of this project an in‑memory index is sufficient.
    """
    def __init__(self, doc_repo: UserDocumentRepository, embed_client: EmbeddingClient):
        self.doc_repo = doc_repo
        self.embed_client = embed_client
        self.index = None  # type: faiss.IndexFlatL2 | None
        self.doc_ids: List[int] = []

    async def build_index(self, user_id: int) -> None:
        """Create a FAISS index for all documents of ``user_id``.

        The index stores embeddings of the whole document content.
        """
        docs: List[UserDocument] = self.doc_repo.get_by_user(user_id)
        if not docs:
            self.index = None
            self.doc_ids = []
            return
        texts = [doc.content for doc in docs]
        embeddings = await self.embed_client.embed(texts)
        vectors = np.array(embeddings).astype("float32")
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors)
        self.doc_ids = [doc.id for doc in docs]

    async def query(self, user_id: int, query: str, top_k: int = 3) -> List[UserDocument]:
        """Return the most relevant documents for ``query``.

        If the index is not built yet it will be built automatically.
        """
        if self.index is None:
            await self.build_index(user_id)
        if self.index is None:
            return []
        query_emb = await self.embed_client.embed([query])
        q_vec = np.array(query_emb).astype("float32")
        distances, indices = self.index.search(q_vec, top_k)
        result_ids = [self.doc_ids[i] for i in indices[0] if i < len(self.doc_ids)]
        return [self.doc_repo.get(doc_id) for doc_id in result_ids if self.doc_repo.get(doc_id) is not None]
