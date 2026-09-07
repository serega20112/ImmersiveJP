from abc import ABC, abstractmethod
from typing import Any


class UnitOfWork(ABC):
    """Порт Unit of Work для управления транзакционной границей."""

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    def repository(self, name: str) -> Any:
        pass
