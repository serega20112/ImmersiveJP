from .base import InfrastructureError


class DatabaseError(InfrastructureError):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class DatabaseTransactionError(DatabaseError):
    pass


class DatabaseRepositoryNotFoundError(DatabaseError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Репозиторий '{name}' не найден в UnitOfWork")
