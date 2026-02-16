"""Projects resource — CRUD + list project prompts."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from prompthub._base import AsyncTransport, SyncTransport
from prompthub._pagination import PaginatedList
from prompthub.types import Project, ProjectDetail, PromptSummary

_PREFIX = "/api/v1/projects"


def _build_create_body(
    *,
    name: str,
    slug: str,
    description: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name, "slug": slug}
    if description is not None:
        body["description"] = description
    return body


def _paginated_projects(data: Any, meta: dict[str, Any] | None) -> PaginatedList[Project]:
    items = [Project(**item) for item in (data or [])]
    meta = meta or {}
    return PaginatedList(
        items=items,
        page=meta.get("page", 1),
        page_size=meta.get("page_size", 20),
        total=meta.get("total", len(items)),
    )


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


class ProjectsResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        slug: str,
        description: str | None = None,
    ) -> Project:
        body = _build_create_body(name=name, slug=slug, description=description)
        data, _ = self._transport.request("POST", _PREFIX, json=body)
        return Project(**data)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[Project]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        data, meta = self._transport.request("GET", _PREFIX, params=params)
        return _paginated_projects(data, meta)

    def get(self, project_id: str | UUID) -> ProjectDetail:
        data, _ = self._transport.request("GET", f"{_PREFIX}/{project_id}")
        return ProjectDetail(**data)

    def list_prompts(
        self,
        project_id: str | UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        data, meta = self._transport.request(
            "GET",
            f"{_PREFIX}/{project_id}/prompts",
            params=params,
        )
        return _paginated_summaries(data, meta)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class AsyncProjectsResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        name: str,
        slug: str,
        description: str | None = None,
    ) -> Project:
        body = _build_create_body(name=name, slug=slug, description=description)
        data, _ = await self._transport.request("POST", _PREFIX, json=body)
        return Project(**data)

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[Project]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        data, meta = await self._transport.request("GET", _PREFIX, params=params)
        return _paginated_projects(data, meta)

    async def get(self, project_id: str | UUID) -> ProjectDetail:
        data, _ = await self._transport.request("GET", f"{_PREFIX}/{project_id}")
        return ProjectDetail(**data)

    async def list_prompts(
        self,
        project_id: str | UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "order": order,
        }
        data, meta = await self._transport.request(
            "GET",
            f"{_PREFIX}/{project_id}/prompts",
            params=params,
        )
        return _paginated_summaries(data, meta)
