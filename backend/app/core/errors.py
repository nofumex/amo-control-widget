from __future__ import annotations


class AppError(RuntimeError):
    def __init__(self, message: str, *, public_message: str | None = None) -> None:
        super().__init__(message)
        self.public_message = public_message or message


class ExternalServiceError(AppError):
    pass


class TenantAuthError(AppError):
    pass
