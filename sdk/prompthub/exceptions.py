"""PromptHub SDK exceptions — maps backend error codes to typed exceptions."""

from __future__ import annotations


class PromptHubError(Exception):
    """Base SDK exception."""

    def __init__(self, code: int, message: str, detail: str | None = None) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.message!r})"


class AuthenticationError(PromptHubError):
    """Invalid or missing API key (40100)."""


class PermissionDeniedError(PromptHubError):
    """Insufficient permissions (40300)."""


class NotFoundError(PromptHubError):
    """Resource not found (40400)."""


class ConflictError(PromptHubError):
    """Resource conflict, e.g. duplicate slug (40900)."""


class CircularDependencyError(PromptHubError):
    """Circular dependency detected in scene pipeline (40901)."""


class ValidationError(PromptHubError):
    """Request validation failed (42200)."""


class TemplateRenderError(PromptHubError):
    """Template rendering failed (42201)."""


class LLMError(PromptHubError):
    """LLM service unavailable (50200)."""


# Backend error code -> SDK exception class
ERROR_MAP: dict[int, type[PromptHubError]] = {
    40100: AuthenticationError,
    40300: PermissionDeniedError,
    40400: NotFoundError,
    40900: ConflictError,
    40901: CircularDependencyError,
    42200: ValidationError,
    42201: TemplateRenderError,
    50200: LLMError,
}
