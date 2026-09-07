from .base import DomainError
from .content import (
    CardAlreadyCompletedError,
    ContentDomainError,
    InvalidBatchNumberError,
    InvalidCardPositionError,
)
from .documents import DocumentDomainError, InvalidDocumentTitleError
from .progress import InvalidCardCountError, InvalidCompletionRateError, ProgressDomainError
from .session import SessionDomainError
from .user import (
    InvalidDisplayNameError,
    InvalidEmailError,
    InvalidPasswordHashError,
    UserAlreadyVerifiedError,
    UserDomainError,
    UserNotOnboardedError,
)
from .value_objects import InvalidIDValueError, InvalidTimestampValueError

__all__ = [
    # Base
    "DomainError",
    # Value objects
    "InvalidIDValueError",
    "InvalidTimestampValueError",
    # User
    "UserDomainError",
    "InvalidEmailError",
    "InvalidDisplayNameError",
    "InvalidPasswordHashError",
    "UserAlreadyVerifiedError",
    "UserNotOnboardedError",
    # Content
    "ContentDomainError",
    "InvalidBatchNumberError",
    "InvalidCardPositionError",
    "CardAlreadyCompletedError",
    # Progress
    "ProgressDomainError",
    "InvalidCardCountError",
    "InvalidCompletionRateError",
    # Session
    "SessionDomainError",
    # Documents
    "DocumentDomainError",
    "InvalidDocumentTitleError",
]
