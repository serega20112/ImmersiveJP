from src.backend.infrastructure.models.user_document_model import UserDocument
from src.backend.infrastructure.repositories.user_document_repository import UserDocumentRepository


class DocumentService:
    """Service for handling user documents.

    Args:
        repo: Repository instance for data access.
    """

    def __init__(self, repo: UserDocumentRepository):
        """Initialize the document service.

        Args:
            repo: Repository instance for data access.
        """
        self.repo = repo

    def upload_document(self, user_id: int, title: str, content: str) -> UserDocument:
        """Create a new document for a user.

        Args:
            user_id: ID of the user.
            title: Title of the document.
            content: Content of the document.

        Returns:
            The created UserDocument instance.
        """
        return self.repo.create(user_id, title, content)

    def list_documents(self, user_id: int) -> list[UserDocument]:
        """Retrieve all documents belonging to a user.

        Args:
            user_id: ID of the user.

        Returns:
            List of user documents.
        """
        return self.repo.get_by_user(user_id)

    def get_document(self, doc_id: int) -> UserDocument | None:
        """Get a single document by its identifier.

        Args:
            doc_id: ID of the document.

        Returns:
            The document, or None if not found.
        """
        return self.repo.get(doc_id)

    def delete_document(self, doc_id: int) -> None:
        """Delete a document.

        Args:
            doc_id: ID of the document to delete.
        """
        self.repo.delete(doc_id)
