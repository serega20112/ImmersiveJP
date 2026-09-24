from .auth import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
    InvalidVerificationCodeError,
)
from .base import ApplicationError, ComponentUnavailableError, ErrorCode
from .documents import InvalidDocumentDataError
from .knowledge import InvalidKnowledgeDataError
from .learning import (
    CardNotFoundError,
    CardOwnershipError,
    CurrentBatchNotCompletedError,
    InvalidSpeechWordsError,
    InvalidTrackWorkSubmissionError,
    LlmRateLimitExceededError,
    NoCompletedCardsError,
    SpeechRateLimitExceededError,
    TrackWorkUnavailableError,
)
from .onboarding import InvalidOnboardingDataError
from .profile import CourseProgramUnavailableError, InvalidMentorMessageError
from .rate_limiting import RateLimitExceededError
from .security import SecurityViolationError

__all__ = [
    "ApplicationError",
    "CardNotFoundError",
    "CardOwnershipError",
    "ComponentUnavailableError",
    "CourseProgramUnavailableError",
    "CurrentBatchNotCompletedError",
    "EmailAlreadyExistsError",
    "EmailNotVerifiedError",
    "ErrorCode",
    "InvalidCredentialsError",
    "InvalidDocumentDataError",
    "InvalidKnowledgeDataError",
    "InvalidMentorMessageError",
    "InvalidOnboardingDataError",
    "InvalidRegistrationDataError",
    "InvalidSpeechWordsError",
    "InvalidTrackWorkSubmissionError",
    "InvalidVerificationCodeError",
    "LlmRateLimitExceededError",
    "NoCompletedCardsError",
    "RateLimitExceededError",
    "SecurityViolationError",
    "SpeechRateLimitExceededError",
    "TrackWorkUnavailableError",
]
