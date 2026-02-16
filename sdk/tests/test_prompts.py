"""Tests for prompts resource — sync and async."""

from __future__ import annotations

from uuid import UUID

import pytest

from prompthub import (
    AsyncPromptHubClient,
    NotFoundError,
    Prompt,
    PromptHubClient,
    PromptSummary,
    RenderResult,
    Version,
)
from tests.conftest import (
    PROJECT_ID,
    PROMPT_DATA,
    PROMPT_ID,
    PROMPT_SUMMARY_DATA,
    RENDER_DATA,
    VERSION_DATA,
    VERSION_ID,
    _RouteRegistry,
    envelope,
    list_envelope,
)

# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestPromptsSync:
    def test_create(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/prompts", envelope(PROMPT_DATA))
        prompt = sync_client.prompts.create(
            name="Test Prompt",
            slug="test-prompt",
            content="Hello {{ name }}",
            project_id=PROJECT_ID,
        )
        assert isinstance(prompt, Prompt)
        assert prompt.id == UUID(PROMPT_ID)
        assert prompt.slug == "test-prompt"

    def test_list(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = sync_client.prompts.list()
        assert len(result) == 1
        assert result.total == 1
        assert isinstance(result.items[0], PromptSummary)

    def test_list_with_slug_filter(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = sync_client.prompts.list(slug="test-prompt", project_id=PROJECT_ID)
        assert len(result) == 1

    def test_get(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("GET", f"/api/v1/prompts/{PROMPT_ID}", envelope(PROMPT_DATA))
        prompt = sync_client.prompts.get(PROMPT_ID)
        assert prompt.name == "Test Prompt"
        assert prompt.content == "Hello {{ name }}"

    def test_get_by_slug(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        routes.add("GET", f"/api/v1/prompts/{PROMPT_ID}", envelope(PROMPT_DATA))
        prompt = sync_client.prompts.get_by_slug("test-prompt")
        assert prompt.slug == "test-prompt"

    def test_get_by_slug_not_found(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("GET", "/api/v1/prompts", list_envelope([], total=0))
        with pytest.raises(NotFoundError, match="No prompt with slug"):
            sync_client.prompts.get_by_slug("nonexistent")

    def test_update(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        updated = {**PROMPT_DATA, "name": "Updated"}
        routes.add("PUT", f"/api/v1/prompts/{PROMPT_ID}", envelope(updated))
        prompt = sync_client.prompts.update(PROMPT_ID, name="Updated")
        assert prompt.name == "Updated"

    def test_delete(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("DELETE", f"/api/v1/prompts/{PROMPT_ID}", envelope())
        sync_client.prompts.delete(PROMPT_ID)  # should not raise

    def test_render(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "POST",
            f"/api/v1/prompts/{PROMPT_ID}/render",
            envelope(RENDER_DATA),
        )
        result = sync_client.prompts.render(PROMPT_ID, variables={"name": "World"})
        assert isinstance(result, RenderResult)
        assert result.rendered_content == "Hello World"
        assert result.variables_used == {"name": "World"}

    def test_share(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        shared = {**PROMPT_DATA, "is_shared": True}
        routes.add("POST", f"/api/v1/prompts/{PROMPT_ID}/share", envelope(shared))
        prompt = sync_client.prompts.share(PROMPT_ID)
        assert prompt.is_shared is True

    def test_list_versions(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/prompts/{PROMPT_ID}/versions",
            envelope([VERSION_DATA]),
        )
        versions = sync_client.prompts.list_versions(PROMPT_ID)
        assert len(versions) == 1
        assert isinstance(versions[0], Version)
        assert versions[0].version == "1.0.0"

    def test_publish(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        new_ver = {**VERSION_DATA, "version": "1.0.1"}
        routes.add(
            "POST",
            f"/api/v1/prompts/{PROMPT_ID}/publish",
            envelope(new_ver),
        )
        version = sync_client.prompts.publish(PROMPT_ID, bump="patch", changelog="fix typo")
        assert version.version == "1.0.1"

    def test_get_version(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/prompts/{PROMPT_ID}/versions/1.0.0",
            envelope(VERSION_DATA),
        )
        version = sync_client.prompts.get_version(PROMPT_ID, "1.0.0")
        assert version.id == UUID(VERSION_ID)


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestPromptsAsync:
    @pytest.mark.asyncio
    async def test_create(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/prompts", envelope(PROMPT_DATA))
        prompt = await async_client.prompts.create(
            name="Test Prompt",
            slug="test-prompt",
            content="Hello {{ name }}",
            project_id=PROJECT_ID,
        )
        assert isinstance(prompt, Prompt)

    @pytest.mark.asyncio
    async def test_get(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add("GET", f"/api/v1/prompts/{PROMPT_ID}", envelope(PROMPT_DATA))
        prompt = await async_client.prompts.get(PROMPT_ID)
        assert prompt.slug == "test-prompt"

    @pytest.mark.asyncio
    async def test_get_by_slug(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        routes.add("GET", f"/api/v1/prompts/{PROMPT_ID}", envelope(PROMPT_DATA))
        prompt = await async_client.prompts.get_by_slug("test-prompt")
        assert prompt.slug == "test-prompt"

    @pytest.mark.asyncio
    async def test_render(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "POST",
            f"/api/v1/prompts/{PROMPT_ID}/render",
            envelope(RENDER_DATA),
        )
        result = await async_client.prompts.render(PROMPT_ID, variables={"name": "World"})
        assert result.rendered_content == "Hello World"

    @pytest.mark.asyncio
    async def test_list_versions(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/prompts/{PROMPT_ID}/versions",
            envelope([VERSION_DATA]),
        )
        versions = await async_client.prompts.list_versions(PROMPT_ID)
        assert len(versions) == 1
