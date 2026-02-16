"""Shared prompts resource — browse shared repository and fork prompts."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from prompthub._base import AsyncTransport, SyncTransport
from prompthub._pagination import PaginatedList
from prompthub.types import Prompt, PromptSummary

_PREFIX = "/api/v1/shared/prompts"


def _paginated_summaries(
    data: Any,
    meta: dict[str, Any] | None,
) -> PaginatedList[PromptSummary]:
    items = [PromptSummary(**item) for item in (data or [])]
    meta = meta or {}
    return PaginatedList(
        items=items,
        page=meta.get("page", 1),
        page_size=meta.get("page_size", 20),
        total=meta.get("total", len(items)),
    )


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


class SharedResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list_prompts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        if search is not None:
            params["search"] = search
        data, meta = self._transport.request("GET", _PREFIX, params=params)
        return _paginated_summaries(data, meta)

    def fork(
        self,
        prompt_id: str | UUID,
        *,
        target_project_id: str | UUID,
        slug: str | None = None,
    ) -> Prompt:
        body: dict[str, Any] = {"target_project_id": str(target_project_id)}
        if slug is not None:
            body["slug"] = slug
        data, _ = self._transport.request("POST", f"{_PREFIX}/{prompt_id}/fork", json=body)
        return Prompt(**data)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class AsyncSharedResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list_prompts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        if search is not None:
            params["search"] = search
        data, meta = await self._transport.request("GET", _PREFIX, params=params)
        return _paginated_summaries(data, meta)

    async def fork(
        self,
        prompt_id: str | UUID,
        *,
        target_project_id: str | UUID,
        slug: str | None = None,
    ) -> Prompt:
        body: dict[str, Any] = {"target_project_id": str(target_project_id)}
        if slug is not None:
            body["slug"] = slug
        data, _ = await self._transport.request(
            "POST",
            f"{_PREFIX}/{prompt_id}/fork",
            json=body,
        )
        return Prompt(**data)
