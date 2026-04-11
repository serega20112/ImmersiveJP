from __future__ import annotations

from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.dependencies.providers import (
    AuthProvidersMixin,
    LearningProvidersMixin,
    OnboardingProvidersMixin,
    ProfileProvidersMixin,
    RepositoryProvidersMixin,
    RootInfrastructureProvidersMixin,
)


class Container(RootInfrastructureProvidersMixin):
    def scope(
        self,
        *,
        session: AsyncSession | None = None,
        session_factory: Callable[[], AsyncSession] | None = None,
        request_state=None,
    ) -> "RequestContainer":
        return RequestContainer(
            root=self,
            session=session,
            session_factory=session_factory,
            request_state=request_state,
        )


class RequestContainer(
    RepositoryProvidersMixin,
    AuthProvidersMixin,
    LearningProvidersMixin,
    OnboardingProvidersMixin,
    ProfileProvidersMixin,
):
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


container = Container()
