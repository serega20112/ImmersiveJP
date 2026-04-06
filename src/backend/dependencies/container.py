from __future__ import annotations

from functools import cached_property
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.cache import KeyValueStore
from src.backend.infrastructure.external import HuggingFaceLLMClient, Mailer, PdfBuilder
from src.backend.infrastructure.security import (
    EmailVerificationStore,
    JWTService,
    PasswordService,
    RateLimiter,
    TokenBlocklist,
)
from src.backend.repository import (
    ContentRepository,
    ProgressRepository,
    SessionRepository,
    UserRepository,
)
from src.backend.services import (
    AuthService,
    DashboardService,
    LearningService,
    OnboardingService,
    ProfileService,
)
from src.backend.use_case.auth import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RegisterUserUseCase,
    ResolveCurrentUserUseCase,
    VerifyEmailUseCase,
)
from src.backend.use_case.dashboard import GetDashboardUseCase
from src.backend.use_case.learning import (
    CompleteCardUseCase,
    ExportCardsToPDFUseCase,
    GenerateCardsUseCase,
    GenerateSpeechPracticeUseCase,
    GetCardPageUseCase,
    GetNextCardsUseCase,
    GetSpeechPracticePageUseCase,
    GetTrackPageUseCase,
    RepairCurrentBatchUseCase,
)
from src.backend.use_case.onboarding import (
    CompleteOnboardingUseCase,
    GetOnboardingPageUseCase,
)
from src.backend.use_case.profile import (
    BuildProgressReportUseCase,
    GenerateAIAdviceUseCase,
)


class Container:
    @cached_property
    def key_value_store(self) -> KeyValueStore:
        return KeyValueStore(
            redis_url=Settings.redis_url if Settings.redis_enabled else None,
            namespace="immersjp",
            required=Settings.redis_required,
        )

    @cached_property
    def password_service(self) -> PasswordService:
        return PasswordService()

    @cached_property
    def jwt_service(self) -> JWTService:
        return JWTService()

    @cached_property
    def token_blocklist(self) -> TokenBlocklist:
        return TokenBlocklist(self.key_value_store)

    @cached_property
    def rate_limiter(self) -> RateLimiter:
        return RateLimiter(self.key_value_store)

    @cached_property
    def email_verification_store(self) -> EmailVerificationStore:
        return EmailVerificationStore(
            self.key_value_store,
            ttl_seconds=Settings.email_verification_expire_minutes * 60,
        )

    @cached_property
    def mailer(self) -> Mailer:
        return Mailer()

    @cached_property
    def llm_client(self) -> HuggingFaceLLMClient:
        return HuggingFaceLLMClient(self.key_value_store)

    @cached_property
    def pdf_builder(self) -> PdfBuilder:
        return PdfBuilder()

    def scope(
        self,
        *,
        session: AsyncSession | None = None,
        session_factory: Callable[[], AsyncSession] | None = None,
        request_state=None,
    ) -> RequestContainer:
        return RequestContainer(
            root=self,
            session=session,
            session_factory=session_factory,
            request_state=request_state,
        )

    async def shutdown(self) -> None:
        await self.llm_client.close()
        await self.key_value_store.close()


class RequestContainer:
    def __init__(
        self,
        root: Container,
        *,
        session: AsyncSession | None = None,
        session_factory: Callable[[], AsyncSession] | None = None,
        request_state=None,
    ):
        self.root = root
        self._session = session
        self._session_factory = session_factory
        self._request_state = request_state

    def _ensure_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        if self._session_factory is None:
            raise RuntimeError("Session factory is not configured")
        self._session = self._session_factory()
        if self._request_state is not None:
            self._request_state.db_session = self._session
        return self._session

    @property
    def session(self) -> AsyncSession:
        return self._ensure_session()

    async def aclose(self) -> None:
        if self._session is None:
            return
        await self._session.close()
        self._session = None
        if self._request_state is not None:
            self._request_state.db_session = None

    @cached_property
    def user_repository(self) -> UserRepository:
        return UserRepository(self.session)

    @cached_property
    def content_repository(self) -> ContentRepository:
        return ContentRepository(self.session)

    @cached_property
    def progress_repository(self) -> ProgressRepository:
        return ProgressRepository(self.session)

    @cached_property
    def session_repository(self) -> SessionRepository:
        return SessionRepository(self.session)

    @cached_property
    def register_user_use_case(self) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            self.user_repository,
            self.root.password_service,
            self.root.email_verification_store,
            self.root.mailer,
        )

    @cached_property
    def verify_email_use_case(self) -> VerifyEmailUseCase:
        return VerifyEmailUseCase(
            self.user_repository,
            self.root.email_verification_store,
        )

    @cached_property
    def login_user_use_case(self) -> LoginUserUseCase:
        return LoginUserUseCase(
            self.user_repository,
            self.root.password_service,
            self.root.jwt_service,
        )

    @cached_property
    def logout_user_use_case(self) -> LogoutUserUseCase:
        return LogoutUserUseCase(self.root.jwt_service, self.root.token_blocklist)

    @cached_property
    def resolve_current_user_use_case(self) -> ResolveCurrentUserUseCase:
        return ResolveCurrentUserUseCase(
            self.user_repository,
            self.root.jwt_service,
            self.root.token_blocklist,
        )

    @cached_property
    def generate_cards_use_case(self) -> GenerateCardsUseCase:
        return GenerateCardsUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
            self.root.llm_client,
            self.root.rate_limiter,
        )

    @cached_property
    def get_track_page_use_case(self) -> GetTrackPageUseCase:
        return GetTrackPageUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
        )

    @cached_property
    def get_card_page_use_case(self) -> GetCardPageUseCase:
        return GetCardPageUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
        )

    @cached_property
    def repair_current_batch_use_case(self) -> RepairCurrentBatchUseCase:
        return RepairCurrentBatchUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
            self.root.llm_client,
        )

    @cached_property
    def complete_card_use_case(self) -> CompleteCardUseCase:
        return CompleteCardUseCase(self.content_repository, self.progress_repository)

    @cached_property
    def get_next_cards_use_case(self) -> GetNextCardsUseCase:
        return GetNextCardsUseCase(
            self.session_repository,
            self.progress_repository,
            self.generate_cards_use_case,
            self.get_track_page_use_case,
        )

    @cached_property
    def export_cards_to_pdf_use_case(self) -> ExportCardsToPDFUseCase:
        return ExportCardsToPDFUseCase(
            self.user_repository,
            self.content_repository,
            self.root.pdf_builder,
        )

    @cached_property
    def get_speech_practice_page_use_case(self) -> GetSpeechPracticePageUseCase:
        return GetSpeechPracticePageUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
        )

    @cached_property
    def generate_speech_practice_use_case(self) -> GenerateSpeechPracticeUseCase:
        return GenerateSpeechPracticeUseCase(
            self.user_repository,
            self.get_speech_practice_page_use_case,
            self.root.llm_client,
            self.root.rate_limiter,
        )

    @cached_property
    def get_onboarding_page_use_case(self) -> GetOnboardingPageUseCase:
        return GetOnboardingPageUseCase()

    @cached_property
    def complete_onboarding_use_case(self) -> CompleteOnboardingUseCase:
        return CompleteOnboardingUseCase(
            self.user_repository,
            self.generate_cards_use_case,
        )

    @cached_property
    def build_progress_report_use_case(self) -> BuildProgressReportUseCase:
        return BuildProgressReportUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
            self.user_repository,
        )

    @cached_property
    def generate_ai_advice_use_case(self) -> GenerateAIAdviceUseCase:
        return GenerateAIAdviceUseCase(self.user_repository, self.root.llm_client)

    @cached_property
    def get_dashboard_use_case(self) -> GetDashboardUseCase:
        return GetDashboardUseCase(
            self.user_repository,
            self.build_progress_report_use_case,
        )

    @cached_property
    def auth_service(self) -> AuthService:
        return AuthService(
            self.register_user_use_case,
            self.verify_email_use_case,
            self.login_user_use_case,
            self.logout_user_use_case,
            self.resolve_current_user_use_case,
        )

    @cached_property
    def onboarding_service(self) -> OnboardingService:
        return OnboardingService(
            self.complete_onboarding_use_case,
            self.get_onboarding_page_use_case,
        )

    @cached_property
    def learning_service(self) -> LearningService:
        return LearningService(
            self.get_track_page_use_case,
            self.get_card_page_use_case,
            self.repair_current_batch_use_case,
            self.complete_card_use_case,
            self.get_next_cards_use_case,
            self.export_cards_to_pdf_use_case,
            self.get_speech_practice_page_use_case,
            self.generate_speech_practice_use_case,
        )

    @cached_property
    def profile_service(self) -> ProfileService:
        return ProfileService(
            self.build_progress_report_use_case,
            self.generate_ai_advice_use_case,
        )

    @cached_property
    def dashboard_service(self) -> DashboardService:
        return DashboardService(self.get_dashboard_use_case)


container = Container()
