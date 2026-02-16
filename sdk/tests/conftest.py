"""Shared fixtures — mock HTTP transport for SDK tests."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from prompthub import AsyncPromptHubClient, PromptHubClient

# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

NOW = "2025-01-15T10:00:00Z"

PROJECT_ID = "11111111-1111-1111-1111-111111111111"
PROMPT_ID = "22222222-2222-2222-2222-222222222222"
SCENE_ID = "33333333-3333-3333-3333-333333333333"
VERSION_ID = "44444444-4444-4444-4444-444444444444"
USER_ID = "55555555-5555-5555-5555-555555555555"

PROMPT_DATA = {
    "id": PROMPT_ID,
    "name": "Test Prompt",
    "slug": "test-prompt",
    "description": "A test prompt",
    "content": "Hello {{ name }}",
    "format": "text",
    "template_engine": "jinja2",
    "variables": [{"name": "name", "type": "string", "required": True}],
    "tags": ["test"],
    "category": "general",
    "project_id": PROJECT_ID,
    "is_shared": False,
    "current_version": "1.0.0",
    "created_by": USER_ID,
    "created_at": NOW,
    "updated_at": NOW,
}

PROMPT_SUMMARY_DATA = {
    "id": PROMPT_ID,
    "name": "Test Prompt",
    "slug": "test-prompt",
    "description": "A test prompt",
    "format": "text",
    "tags": ["test"],
    "category": "general",
    "project_id": PROJECT_ID,
    "is_shared": False,
    "current_version": "1.0.0",
    "created_at": NOW,
    "updated_at": NOW,
}

VERSION_DATA = {
    "id": VERSION_ID,
    "prompt_id": PROMPT_ID,
    "version": "1.0.0",
    "content": "Hello {{ name }}",
    "variables": [],
    "changelog": "Initial version",
    "status": "published",
    "created_by": USER_ID,
    "created_at": NOW,
}

PROJECT_DATA = {
    "id": PROJECT_ID,
    "name": "Test Project",
    "slug": "test-project",
    "description": "A test project",
    "created_by": USER_ID,
    "created_at": NOW,
    "updated_at": NOW,
}

PROJECT_DETAIL_DATA = {
    **PROJECT_DATA,
    "prompt_count": 5,
    "scene_count": 2,
}

SCENE_DATA = {
    "id": SCENE_ID,
    "name": "Test Scene",
    "slug": "test-scene",
    "description": "A test scene",
    "project_id": PROJECT_ID,
    "pipeline": {"steps": []},
    "merge_strategy": "concat",
    "separator": "\n\n",
    "output_format": None,
    "created_by": USER_ID,
    "created_at": NOW,
    "updated_at": NOW,
}

RESOLVE_DATA = {
    "scene_id": SCENE_ID,
    "scene_name": "Test Scene",
    "merge_strategy": "concat",
    "final_content": "Rendered prompt content",
    "steps": [
        {
            "step_id": "step-1",
            "prompt_id": PROMPT_ID,
            "prompt_name": "Test Prompt",
            "version": "1.0.0",
            "rendered_content": "Rendered prompt content",
            "skipped": False,
            "skip_reason": None,
        }
    ],
    "total_token_estimate": 42,
}

RENDER_DATA = {
    "prompt_id": PROMPT_ID,
    "version": "1.0.0",
    "rendered_content": "Hello World",
    "variables_used": {"name": "World"},
}

DEPENDENCY_GRAPH_DATA = {
    "nodes": [
        {
            "id": PROMPT_ID,
            "name": "Test Prompt",
            "project_id": PROJECT_ID,
            "version": "1.0.0",
            "is_shared": False,
        }
    ],
    "edges": [],
}


# ---------------------------------------------------------------------------
# Envelope helper
# ---------------------------------------------------------------------------


def envelope(
    data: Any = None,
    *,
    meta: dict[str, Any] | None = None,
    code: int = 0,
    message: str = "success",
    status_code: int = 200,
) -> httpx.Response:
    body: dict[str, Any] = {"code": code, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return httpx.Response(status_code=status_code, json=body)


def list_envelope(
    data: list[Any],
    *,
    page: int = 1,
    page_size: int = 20,
    total: int | None = None,
) -> httpx.Response:
    return envelope(
        data,
        meta={"page": page, "page_size": page_size, "total": total or len(data)},
    )


def error_envelope(
    code: int,
    message: str,
    *,
    status_code: int = 400,
    detail: str | None = None,
) -> httpx.Response:
    body: dict[str, Any] = {"code": code, "message": message}
    if detail:
        body["detail"] = detail
    return httpx.Response(status_code=status_code, json=body)


# ---------------------------------------------------------------------------
# Route registry for mock transport
# ---------------------------------------------------------------------------


class _RouteRegistry:
    """Simple request → response router for tests."""

    def __init__(self) -> None:
        self._routes: list[tuple[str, str, httpx.Response]] = []
        self._default = envelope()

    def add(self, method: str, path: str, response: httpx.Response) -> None:
        self._routes.append((method.upper(), path, response))

    def match(self, request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.raw_path.decode().split("?")[0]
        for m, p, r in self._routes:
            if m == method and path == p:
                return r
        return self._default


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def routes() -> _RouteRegistry:
    return _RouteRegistry()


@pytest.fixture()
def sync_client(routes: _RouteRegistry) -> PromptHubClient:
    transport = httpx.MockTransport(routes.match)
    client = PromptHubClient(base_url="http://test", api_key="ph-test-key")
    # Swap internal httpx client to use mock transport
    client._transport._http = httpx.Client(
        transport=transport,
        base_url="http://test",
        headers=client._transport._headers(),
    )
    return client


@pytest.fixture()
def async_client(routes: _RouteRegistry) -> AsyncPromptHubClient:
    transport = httpx.MockTransport(routes.match)
    client = AsyncPromptHubClient(base_url="http://test", api_key="ph-test-key")
    client._transport._http = httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=client._transport._headers(),
    )
    return client
