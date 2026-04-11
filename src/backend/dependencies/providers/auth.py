from __future__ import annotations

from functools import cached_property

from src.backend.services import AuthService
from src.backend.use_case.auth import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RegisterUserUseCase,
    ResolveCurrentUserUseCase,
    VerifyEmailUseCase,
)


class AuthProvidersMixin:
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
    def auth_service(self) -> AuthService:
        return AuthService(
            self.register_user_use_case,
            self.verify_email_use_case,
            self.login_user_use_case,
            self.logout_user_use_case,
            self.resolve_current_user_use_case,
        )
