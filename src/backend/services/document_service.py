from typing import List

from src.backend.infrastructure.repositories.user_document_repository import UserDocumentRepository
from src.backend.infrastructure.models.user_document_model import UserDocument

class DocumentService:
    """Service for handling user documents.

    Args:
        repo: Repository instance for data access.
    """
    def __init__(self, repo: UserDocumentRepository):
        self.repo = repo

    def upload_document(self, user_id: int, title: str, content: str) -> UserDocument:
        """Create a new document for a user.

        Returns:
            The created :class:`UserDocument` instance.
        """
        return self.repo.create(user_id, title, content)

    def list_documents(self, user_id: int) -> List[UserDocument]:
        """Retrieve all documents belonging to a user.
        """
        return self.repo.get_by_user(user_id)

    def get_document(self, doc_id: int) -> UserDocument | None:
        """Get a single document by its identifier.
        """
        return self.repo.get(doc_id)

    def delete_document(self, doc_id: int) -> None:
        """Delete a document.
        """
        self.repo.delete(doc_id)
