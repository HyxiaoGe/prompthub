"""Tests for projects resource — sync and async."""

from __future__ import annotations

from uuid import UUID

import pytest

from prompthub import (
    AsyncPromptHubClient,
    Project,
    ProjectDetail,
    PromptHubClient,
    PromptSummary,
    PublishedPromptBundle,
)
from tests.conftest import (
    PROJECT_DATA,
    PROJECT_DETAIL_DATA,
    PROJECT_ID,
    PROMPT_SUMMARY_DATA,
    PUBLISHED_BUNDLE_DATA,
    _RouteRegistry,
    envelope,
    list_envelope,
)

# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestProjectsSync:
    def test_get_published_bundle(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/projects/by-slug/test-project/prompts/published",
            envelope(PUBLISHED_BUNDLE_DATA),
        )

        bundle = sync_client.projects.get_published_bundle("test-project")

        assert isinstance(bundle, PublishedPromptBundle)
        assert bundle.revision == "a" * 64
        assert bundle.prompts[0].slug == "test-prompt"
        assert bundle.prompts[0].content == "Hello {{ name }}"

    def test_create(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/projects", envelope(PROJECT_DATA))
        project = sync_client.projects.create(name="Test Project", slug="test-project")
        assert isinstance(project, Project)
        assert project.id == UUID(PROJECT_ID)
        assert project.slug == "test-project"

    def test_list(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("GET", "/api/v1/projects", list_envelope([PROJECT_DATA], total=1))
        result = sync_client.projects.list()
        assert len(result) == 1
        assert result.total == 1
        assert isinstance(result.items[0], Project)

    def test_get(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/projects/{PROJECT_ID}",
            envelope(PROJECT_DETAIL_DATA),
        )
        project = sync_client.projects.get(PROJECT_ID)
        assert isinstance(project, ProjectDetail)
        assert project.prompt_count == 5
        assert project.scene_count == 2

    def test_list_prompts(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/projects/{PROJECT_ID}/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = sync_client.projects.list_prompts(PROJECT_ID)
        assert len(result) == 1
        assert isinstance(result.items[0], PromptSummary)


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestProjectsAsync:
    @pytest.mark.asyncio
    async def test_get_published_bundle(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/projects/by-slug/test-project/prompts/published",
            envelope(PUBLISHED_BUNDLE_DATA),
        )

        bundle = await async_client.projects.get_published_bundle("test-project")

        assert isinstance(bundle, PublishedPromptBundle)
        assert bundle.prompts[0].version == "1.0.0"

    @pytest.mark.asyncio
    async def test_create(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/projects", envelope(PROJECT_DATA))
        project = await async_client.projects.create(name="Test Project", slug="test-project")
        assert isinstance(project, Project)

    @pytest.mark.asyncio
    async def test_get(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/projects/{PROJECT_ID}",
            envelope(PROJECT_DETAIL_DATA),
        )
        project = await async_client.projects.get(PROJECT_ID)
        assert isinstance(project, ProjectDetail)
        assert project.prompt_count == 5

    @pytest.mark.asyncio
    async def test_list_prompts(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/projects/{PROJECT_ID}/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = await async_client.projects.list_prompts(PROJECT_ID)
        assert len(result) == 1
