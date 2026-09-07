"""Схемы форм и запросов HTTP-слоя презентации.

Схемы описывают транспортный формат (формы, query-параметры) и отделяют
роуты от сырых полей ``Form()``/``Query()``. Преобразование схемы в DTO
прикладного слоя происходит в роуте.
"""

from .auth import LoginForm, RegistrationForm, VerificationForm
from .documents import DocumentAddForm
from .knowledge import KnowledgeGenerateForm, KnowledgeSubmitForm
from .learning import CompleteCardForm, SpeechPracticeForm, TrackQuery
from .mentor import MentorMessageForm, VoiceInputResponse
from .onboarding import OnboardingForm
from .system import SystemHealthResponse

__all__ = [
    "CompleteCardForm",
    "DocumentAddForm",
    "KnowledgeGenerateForm",
    "KnowledgeSubmitForm",
    "LoginForm",
    "MentorMessageForm",
    "OnboardingForm",
    "RegistrationForm",
    "SpeechPracticeForm",
    "SystemHealthResponse",
    "TrackQuery",
    "VerificationForm",
    "VoiceInputResponse",
]
