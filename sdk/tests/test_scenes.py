"""Tests for scenes resource — sync and async."""

from __future__ import annotations

from uuid import UUID

import pytest

from prompthub import (
    AsyncPromptHubClient,
    DependencyGraph,
    PromptHubClient,
    Scene,
    SceneResolveResult,
)
from tests.conftest import (
    DEPENDENCY_GRAPH_DATA,
    PROJECT_ID,
    PROMPT_ID,
    RESOLVE_DATA,
    SCENE_DATA,
    SCENE_ID,
    _RouteRegistry,
    envelope,
    list_envelope,
)

# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestScenesSync:
    def test_create(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/scenes", envelope(SCENE_DATA))
        scene = sync_client.scenes.create(
            name="Test Scene",
            slug="test-scene",
            project_id=PROJECT_ID,
            pipeline={"steps": []},
        )
        assert isinstance(scene, Scene)
        assert scene.id == UUID(SCENE_ID)

    def test_list(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("GET", "/api/v1/scenes", list_envelope([SCENE_DATA], total=1))
        result = sync_client.scenes.list()
        assert len(result) == 1
        assert result.total == 1
        assert isinstance(result.items[0], Scene)

    def test_get(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("GET", f"/api/v1/scenes/{SCENE_ID}", envelope(SCENE_DATA))
        scene = sync_client.scenes.get(SCENE_ID)
        assert scene.name == "Test Scene"
        assert scene.merge_strategy == "concat"

    def test_update(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        updated = {**SCENE_DATA, "name": "Updated Scene"}
        routes.add("PUT", f"/api/v1/scenes/{SCENE_ID}", envelope(updated))
        scene = sync_client.scenes.update(SCENE_ID, name="Updated Scene")
        assert scene.name == "Updated Scene"

    def test_delete(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add("DELETE", f"/api/v1/scenes/{SCENE_ID}", envelope())
        sync_client.scenes.delete(SCENE_ID)  # should not raise

    def test_resolve(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "POST",
            f"/api/v1/scenes/{SCENE_ID}/resolve",
            envelope(RESOLVE_DATA),
        )
        result = sync_client.scenes.resolve(SCENE_ID, variables={"style": "watercolor"})
        assert isinstance(result, SceneResolveResult)
        assert result.final_content == "Rendered prompt content"
        assert len(result.steps) == 1
        assert result.steps[0].step_id == "step-1"
        assert result.total_token_estimate == 42

    def test_resolve_with_caller_system(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "POST",
            f"/api/v1/scenes/{SCENE_ID}/resolve",
            envelope(RESOLVE_DATA),
        )
        result = sync_client.scenes.resolve(
            SCENE_ID,
            variables={},
            caller_system="audio-service",
        )
        assert isinstance(result, SceneResolveResult)

    def test_dependencies(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/scenes/{SCENE_ID}/dependencies",
            envelope(DEPENDENCY_GRAPH_DATA),
        )
        graph = sync_client.scenes.dependencies(SCENE_ID)
        assert isinstance(graph, DependencyGraph)
        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == UUID(PROMPT_ID)


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestScenesAsync:
    @pytest.mark.asyncio
    async def test_create(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add("POST", "/api/v1/scenes", envelope(SCENE_DATA))
        scene = await async_client.scenes.create(
            name="Test Scene",
            slug="test-scene",
            project_id=PROJECT_ID,
            pipeline={"steps": []},
        )
        assert isinstance(scene, Scene)

    @pytest.mark.asyncio
    async def test_resolve(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "POST",
            f"/api/v1/scenes/{SCENE_ID}/resolve",
            envelope(RESOLVE_DATA),
        )
        result = await async_client.scenes.resolve(SCENE_ID, variables={"style": "oil"})
        assert result.final_content == "Rendered prompt content"
        assert len(result.steps) == 1

    @pytest.mark.asyncio
    async def test_dependencies(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            f"/api/v1/scenes/{SCENE_ID}/dependencies",
            envelope(DEPENDENCY_GRAPH_DATA),
        )
        graph = await async_client.scenes.dependencies(SCENE_ID)
        assert isinstance(graph, DependencyGraph)
