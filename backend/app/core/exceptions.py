class AppError(Exception):
    """Base application error."""

    def __init__(self, code: int, message: str, detail: str | None = None, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", detail: str | None = None) -> None:
        super().__init__(code=40400, message=message, detail=detail, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", detail: str | None = None) -> None:
        super().__init__(code=42200, message=message, detail=detail, status_code=422)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict", detail: str | None = None) -> None:
        super().__init__(code=40900, message=message, detail=detail, status_code=409)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required", detail: str | None = None) -> None:
        super().__init__(code=40100, message=message, detail=detail, status_code=401)


class PermissionError(AppError):
    def __init__(self, message: str = "Permission denied", detail: str | None = None) -> None:
        super().__init__(code=40300, message=message, detail=detail, status_code=403)


class CircularDependencyError(AppError):
    def __init__(self, message: str = "Circular dependency detected", detail: str | None = None) -> None:
        super().__init__(code=40901, message=message, detail=detail, status_code=409)
