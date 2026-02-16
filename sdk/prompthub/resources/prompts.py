"""Prompts resource — CRUD, render, share, versions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from prompthub._base import AsyncTransport, SyncTransport
from prompthub._pagination import PaginatedList
from prompthub.exceptions import NotFoundError
from prompthub.types import Prompt, PromptSummary, RenderResult, Version

_PREFIX = "/api/v1/prompts"


def _build_list_params(
    *,
    page: int,
    page_size: int,
    project_id: str | UUID | None,
    slug: str | None,
    tags: list[str] | None,
    category: str | None,
    is_shared: bool | None,
    search: str | None,
    sort_by: str,
    order: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "order": order,
    }
    if project_id is not None:
        params["project_id"] = str(project_id)
    if slug is not None:
        params["slug"] = slug
    if tags:
        params["tags"] = ",".join(tags)
    if category is not None:
        params["category"] = category
    if is_shared is not None:
        params["is_shared"] = is_shared
    if search is not None:
        params["search"] = search
    return params


def _build_create_body(
    *,
    name: str,
    slug: str,
    content: str,
    project_id: str | UUID,
    description: str | None,
    format: str,
    template_engine: str,
    variables: list[dict[str, Any]] | None,
    tags: list[str] | None,
    category: str | None,
    is_shared: bool,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "slug": slug,
        "content": content,
        "project_id": str(project_id),
        "format": format,
        "template_engine": template_engine,
        "is_shared": is_shared,
    }
    if description is not None:
        body["description"] = description
    if variables is not None:
        body["variables"] = variables
    if tags is not None:
        body["tags"] = tags
    if category is not None:
        body["category"] = category
    return body


def _build_update_body(**kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is not None:
            if key == "project_id":
                body[key] = str(value)
            else:
                body[key] = value
    return body


def _build_publish_body(
    *,
    bump: str,
    changelog: str | None,
    content: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"bump": bump}
    if changelog is not None:
        body["changelog"] = changelog
    if content is not None:
        body["content"] = content
    return body


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


class PromptsResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        slug: str,
        content: str,
        project_id: str | UUID,
        description: str | None = None,
        format: str = "text",
        template_engine: str = "jinja2",
        variables: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        is_shared: bool = False,
    ) -> Prompt:
        body = _build_create_body(
            name=name,
            slug=slug,
            content=content,
            project_id=project_id,
            description=description,
            format=format,
            template_engine=template_engine,
            variables=variables,
            tags=tags,
            category=category,
            is_shared=is_shared,
        )
        data, _ = self._transport.request("POST", _PREFIX, json=body)
        result = Prompt(**data)
        if self._transport.cache:
            self._transport.cache.invalidate_prefix("prompts:")
        return result

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        project_id: str | UUID | None = None,
        slug: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        is_shared: bool | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params = _build_list_params(
            page=page,
            page_size=page_size,
            project_id=project_id,
            slug=slug,
            tags=tags,
            category=category,
            is_shared=is_shared,
            search=search,
            sort_by=sort_by,
            order=order,
        )
        data, meta = self._transport.request("GET", _PREFIX, params=params)
        return _paginated_summaries(data, meta)

    def get(self, prompt_id: str | UUID) -> Prompt:
        cache = self._transport.cache
        cache_key = f"prompts:{prompt_id}"
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        data, _ = self._transport.request("GET", f"{_PREFIX}/{prompt_id}")
        result = Prompt(**data)
        if cache:
            cache.set(cache_key, result)
        return result

    def get_by_slug(
        self,
        slug: str,
        *,
        project_id: str | UUID | None = None,
    ) -> Prompt:
        """Look up a prompt by exact slug (most common business-system pattern)."""
        results = self.list(slug=slug, project_id=project_id, page_size=1)
        if not results.items:
            raise NotFoundError(code=40400, message=f"No prompt with slug '{slug}'")
        return self.get(results.items[0].id)

    def update(self, prompt_id: str | UUID, **kwargs: Any) -> Prompt:
        body = _build_update_body(**kwargs)
        data, _ = self._transport.request("PUT", f"{_PREFIX}/{prompt_id}", json=body)
        result = Prompt(**data)
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return result

    def delete(self, prompt_id: str | UUID) -> None:
        self._transport.request("DELETE", f"{_PREFIX}/{prompt_id}")
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")

    def render(
        self,
        prompt_id: str | UUID,
        variables: dict[str, Any] | None = None,
    ) -> RenderResult:
        body = {"variables": variables or {}}
        data, _ = self._transport.request("POST", f"{_PREFIX}/{prompt_id}/render", json=body)
        return RenderResult(**data)

    def share(self, prompt_id: str | UUID) -> Prompt:
        data, _ = self._transport.request("POST", f"{_PREFIX}/{prompt_id}/share")
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return Prompt(**data)

    def list_versions(self, prompt_id: str | UUID) -> list[Version]:
        data, _ = self._transport.request("GET", f"{_PREFIX}/{prompt_id}/versions")
        return [Version(**v) for v in (data or [])]

    def publish(
        self,
        prompt_id: str | UUID,
        *,
        bump: str = "patch",
        changelog: str | None = None,
        content: str | None = None,
    ) -> Version:
        body = _build_publish_body(bump=bump, changelog=changelog, content=content)
        data, _ = self._transport.request("POST", f"{_PREFIX}/{prompt_id}/publish", json=body)
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return Version(**data)

    def get_version(self, prompt_id: str | UUID, version: str) -> Version:
        data, _ = self._transport.request("GET", f"{_PREFIX}/{prompt_id}/versions/{version}")
        return Version(**data)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class AsyncPromptsResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        name: str,
        slug: str,
        content: str,
        project_id: str | UUID,
        description: str | None = None,
        format: str = "text",
        template_engine: str = "jinja2",
        variables: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        is_shared: bool = False,
    ) -> Prompt:
        body = _build_create_body(
            name=name,
            slug=slug,
            content=content,
            project_id=project_id,
            description=description,
            format=format,
            template_engine=template_engine,
            variables=variables,
            tags=tags,
            category=category,
            is_shared=is_shared,
        )
        data, _ = await self._transport.request("POST", _PREFIX, json=body)
        result = Prompt(**data)
        if self._transport.cache:
            self._transport.cache.invalidate_prefix("prompts:")
        return result

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        project_id: str | UUID | None = None,
        slug: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        is_shared: bool | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[PromptSummary]:
        params = _build_list_params(
            page=page,
            page_size=page_size,
            project_id=project_id,
            slug=slug,
            tags=tags,
            category=category,
            is_shared=is_shared,
            search=search,
            sort_by=sort_by,
            order=order,
        )
        data, meta = await self._transport.request("GET", _PREFIX, params=params)
        return _paginated_summaries(data, meta)

    async def get(self, prompt_id: str | UUID) -> Prompt:
        cache = self._transport.cache
        cache_key = f"prompts:{prompt_id}"
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        data, _ = await self._transport.request("GET", f"{_PREFIX}/{prompt_id}")
        result = Prompt(**data)
        if cache:
            cache.set(cache_key, result)
        return result

    async def get_by_slug(
        self,
        slug: str,
        *,
        project_id: str | UUID | None = None,
    ) -> Prompt:
        """Look up a prompt by exact slug (most common business-system pattern)."""
        results = await self.list(slug=slug, project_id=project_id, page_size=1)
        if not results.items:
            raise NotFoundError(code=40400, message=f"No prompt with slug '{slug}'")
        return await self.get(results.items[0].id)

    async def update(self, prompt_id: str | UUID, **kwargs: Any) -> Prompt:
        body = _build_update_body(**kwargs)
        data, _ = await self._transport.request("PUT", f"{_PREFIX}/{prompt_id}", json=body)
        result = Prompt(**data)
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return result

    async def delete(self, prompt_id: str | UUID) -> None:
        await self._transport.request("DELETE", f"{_PREFIX}/{prompt_id}")
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")

    async def render(
        self,
        prompt_id: str | UUID,
        variables: dict[str, Any] | None = None,
    ) -> RenderResult:
        body = {"variables": variables or {}}
        data, _ = await self._transport.request(
            "POST",
            f"{_PREFIX}/{prompt_id}/render",
            json=body,
        )
        return RenderResult(**data)

    async def share(self, prompt_id: str | UUID) -> Prompt:
        data, _ = await self._transport.request("POST", f"{_PREFIX}/{prompt_id}/share")
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return Prompt(**data)

    async def list_versions(self, prompt_id: str | UUID) -> list[Version]:
        data, _ = await self._transport.request("GET", f"{_PREFIX}/{prompt_id}/versions")
        return [Version(**v) for v in (data or [])]

    async def publish(
        self,
        prompt_id: str | UUID,
        *,
        bump: str = "patch",
        changelog: str | None = None,
        content: str | None = None,
    ) -> Version:
        body = _build_publish_body(bump=bump, changelog=changelog, content=content)
        data, _ = await self._transport.request(
            "POST",
            f"{_PREFIX}/{prompt_id}/publish",
            json=body,
        )
        if self._transport.cache:
            self._transport.cache.invalidate(f"prompts:{prompt_id}")
        return Version(**data)

    async def get_version(self, prompt_id: str | UUID, version: str) -> Version:
        data, _ = await self._transport.request(
            "GET",
            f"{_PREFIX}/{prompt_id}/versions/{version}",
        )
        return Version(**data)
