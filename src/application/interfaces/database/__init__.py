"""Порты репозиториев слоя приложения."""

from .base import ReadRepositoryPort, RepositoryPort, UnitOfWork, WriteRepositoryPort
from .content import LearningCardRepositoryPort
from .course import CourseRepositoryPort
from .mentor import MentorRepositoryPort
from .progress import ProgressRepositoryPort
from .session import LearningSessionRepositoryPort
from .skill_area import SkillAreaRepositoryPort
from .user import UserRepositoryPort
from .user_document import UserDocumentRepositoryPort

__all__ = [
    "CourseRepositoryPort",
    "LearningCardRepositoryPort",
    "LearningSessionRepositoryPort",
    "MentorRepositoryPort",
    "ProgressRepositoryPort",
    "ReadRepositoryPort",
    "RepositoryPort",
    "SkillAreaRepositoryPort",
    "UnitOfWork",
    "UserDocumentRepositoryPort",
    "UserRepositoryPort",
    "WriteRepositoryPort",
]
