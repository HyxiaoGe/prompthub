"""Tests for shared resource — sync and async."""

from __future__ import annotations

from uuid import UUID

import pytest

from prompthub import AsyncPromptHubClient, Prompt, PromptHubClient, PromptSummary
from tests.conftest import (
    PROJECT_ID,
    PROMPT_DATA,
    PROMPT_ID,
    PROMPT_SUMMARY_DATA,
    _RouteRegistry,
    envelope,
    list_envelope,
)

# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestSharedSync:
    def test_list_prompts(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/shared/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = sync_client.shared.list_prompts()
        assert len(result) == 1
        assert isinstance(result.items[0], PromptSummary)

    def test_list_prompts_with_search(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/shared/prompts",
            list_envelope([], total=0),
        )
        result = sync_client.shared.list_prompts(search="nonexistent")
        assert len(result) == 0

    def test_fork(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        forked = {**PROMPT_DATA, "project_id": PROJECT_ID}
        routes.add(
            "POST",
            f"/api/v1/shared/prompts/{PROMPT_ID}/fork",
            envelope(forked),
        )
        prompt = sync_client.shared.fork(PROMPT_ID, target_project_id=PROJECT_ID)
        assert isinstance(prompt, Prompt)
        assert prompt.id == UUID(PROMPT_ID)

    def test_fork_with_slug_override(
        self,
        routes: _RouteRegistry,
        sync_client: PromptHubClient,
    ) -> None:
        forked = {**PROMPT_DATA, "slug": "my-copy"}
        routes.add(
            "POST",
            f"/api/v1/shared/prompts/{PROMPT_ID}/fork",
            envelope(forked),
        )
        prompt = sync_client.shared.fork(
            PROMPT_ID,
            target_project_id=PROJECT_ID,
            slug="my-copy",
        )
        assert prompt.slug == "my-copy"


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestSharedAsync:
    @pytest.mark.asyncio
    async def test_list_prompts(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        routes.add(
            "GET",
            "/api/v1/shared/prompts",
            list_envelope([PROMPT_SUMMARY_DATA], total=1),
        )
        result = await async_client.shared.list_prompts()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fork(
        self,
        routes: _RouteRegistry,
        async_client: AsyncPromptHubClient,
    ) -> None:
        forked = {**PROMPT_DATA, "project_id": PROJECT_ID}
        routes.add(
            "POST",
            f"/api/v1/shared/prompts/{PROMPT_ID}/fork",
            envelope(forked),
        )
        prompt = await async_client.shared.fork(PROMPT_ID, target_project_id=PROJECT_ID)
        assert isinstance(prompt, Prompt)
