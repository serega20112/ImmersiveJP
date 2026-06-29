from typing import List, Optional

from sqlalchemy.orm import Session

from src.backend.infrastructure.models.user_document_model import UserDocument
from src.backend.infrastructure.models.user_model import UserModel

class UserDocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, title: str, content: str) -> UserDocument:
        doc = UserDocument(user_id=user_id, title=title, content=content)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_user(self, user_id: int) -> List[UserDocument]:
        return self.db.query(UserDocument).filter(UserDocument.user_id == user_id).all()

    def get(self, doc_id: int) -> Optional[UserDocument]:
        return self.db.query(UserDocument).filter(UserDocument.id == doc_id).first()

    def delete(self, doc_id: int) -> None:
        doc = self.get(doc_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
