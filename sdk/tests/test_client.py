"""Client-level tests: init, auth header, envelope unwrap, error mapping."""

from __future__ import annotations

import pytest

from prompthub import (
    AsyncPromptHubClient,
    AuthenticationError,
    CircularDependencyError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    PromptHubClient,
    PromptHubError,
    TemplateRenderError,
    ValidationError,
)
from tests.conftest import _RouteRegistry, error_envelope

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestClientInit:
    def test_sync_client_has_all_resources(self) -> None:
        client = PromptHubClient(base_url="http://x", api_key="k")
        assert hasattr(client, "prompts")
        assert hasattr(client, "scenes")
        assert hasattr(client, "projects")
        assert hasattr(client, "shared")

    def test_async_client_has_all_resources(self) -> None:
        client = AsyncPromptHubClient(base_url="http://x", api_key="k")
        assert hasattr(client, "prompts")
        assert hasattr(client, "scenes")
        assert hasattr(client, "projects")
        assert hasattr(client, "shared")

    def test_auth_header_injected(self) -> None:
        client = PromptHubClient(base_url="http://x", api_key="my-secret")
        assert client._transport._http.headers["authorization"] == "Bearer my-secret"

    def test_context_manager(self) -> None:
        with PromptHubClient(base_url="http://x", api_key="k") as client:
            assert client.prompts is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with AsyncPromptHubClient(base_url="http://x", api_key="k") as client:
            assert client.prompts is not None

    def test_trailing_slash_stripped(self) -> None:
        client = PromptHubClient(base_url="http://x:8000/", api_key="k")
        assert client._transport._base_url == "http://x:8000"


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


class TestErrorMapping:
    @pytest.mark.parametrize(
        "error_code,status_code,exc_cls",
        [
            (40100, 401, AuthenticationError),
            (40300, 403, PermissionDeniedError),
            (40400, 404, NotFoundError),
            (40900, 409, ConflictError),
            (40901, 409, CircularDependencyError),
            (42200, 422, ValidationError),
            (42201, 422, TemplateRenderError),
        ],
    )
    def test_error_code_maps_to_exception(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
        error_code: int,
        status_code: int,
        exc_cls: type[PromptHubError],
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts/bad",
            error_envelope(error_code, "test error", status_code=status_code),
        )
        with pytest.raises(exc_cls) as exc_info:
            sync_client.prompts.get("bad")
        assert exc_info.value.code == error_code
        assert exc_info.value.message == "test error"

    def test_unknown_error_code_raises_base(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts/bad",
            error_envelope(99999, "unknown", status_code=500),
        )
        with pytest.raises(PromptHubError) as exc_info:
            sync_client.prompts.get("bad")
        assert exc_info.value.code == 99999

    def test_error_detail_preserved(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts/bad",
            error_envelope(40400, "Not found", status_code=404, detail="No prompt with id 'bad'"),
        )
        with pytest.raises(NotFoundError) as exc_info:
            sync_client.prompts.get("bad")
        assert exc_info.value.detail == "No prompt with id 'bad'"

    @pytest.mark.asyncio
    async def test_async_error_mapping(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts/bad",
            error_envelope(40400, "Not found", status_code=404),
        )
        with pytest.raises(NotFoundError):
            await async_client.prompts.get("bad")
