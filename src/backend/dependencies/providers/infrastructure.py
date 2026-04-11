from __future__ import annotations

from functools import cached_property

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


class RootInfrastructureProvidersMixin:
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

    async def shutdown(self) -> None:
        await self.llm_client.close()
        await self.key_value_store.close()
