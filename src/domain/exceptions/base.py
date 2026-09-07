class DomainError(Exception):
    """Базовая ошибка доменного слоя."""

    def __init__(self, message: str, *, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
