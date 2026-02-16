"""Scenes resource — CRUD, resolve, dependencies."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from prompthub._base import AsyncTransport, SyncTransport
from prompthub._pagination import PaginatedList
from prompthub.types import DependencyGraph, Scene, SceneResolveResult

_PREFIX = "/api/v1/scenes"


def _build_list_params(
    *,
    page: int,
    page_size: int,
    project_id: str | UUID | None,
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
    return params


def _build_create_body(
    *,
    name: str,
    slug: str,
    project_id: str | UUID,
    pipeline: dict[str, Any],
    description: str | None,
    merge_strategy: str,
    separator: str,
    output_format: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "slug": slug,
        "project_id": str(project_id),
        "pipeline": pipeline,
        "merge_strategy": merge_strategy,
        "separator": separator,
    }
    if description is not None:
        body["description"] = description
    if output_format is not None:
        body["output_format"] = output_format
    return body


def _build_update_body(**kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is not None:
            body[key] = value
    return body


def _paginated_scenes(data: Any, meta: dict[str, Any] | None) -> PaginatedList[Scene]:
    items = [Scene(**item) for item in (data or [])]
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


class ScenesResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        slug: str,
        project_id: str | UUID,
        pipeline: dict[str, Any],
        description: str | None = None,
        merge_strategy: str = "concat",
        separator: str = "\n\n",
        output_format: str | None = None,
    ) -> Scene:
        body = _build_create_body(
            name=name,
            slug=slug,
            project_id=project_id,
            pipeline=pipeline,
            description=description,
            merge_strategy=merge_strategy,
            separator=separator,
            output_format=output_format,
        )
        data, _ = self._transport.request("POST", _PREFIX, json=body)
        return Scene(**data)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        project_id: str | UUID | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[Scene]:
        params = _build_list_params(
            page=page,
            page_size=page_size,
            project_id=project_id,
            sort_by=sort_by,
            order=order,
        )
        data, meta = self._transport.request("GET", _PREFIX, params=params)
        return _paginated_scenes(data, meta)

    def get(self, scene_id: str | UUID) -> Scene:
        cache = self._transport.cache
        cache_key = f"scenes:{scene_id}"
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        data, _ = self._transport.request("GET", f"{_PREFIX}/{scene_id}")
        result = Scene(**data)
        if cache:
            cache.set(cache_key, result)
        return result

    def update(self, scene_id: str | UUID, **kwargs: Any) -> Scene:
        body = _build_update_body(**kwargs)
        data, _ = self._transport.request("PUT", f"{_PREFIX}/{scene_id}", json=body)
        if self._transport.cache:
            self._transport.cache.invalidate(f"scenes:{scene_id}")
        return Scene(**data)

    def delete(self, scene_id: str | UUID) -> None:
        self._transport.request("DELETE", f"{_PREFIX}/{scene_id}")
        if self._transport.cache:
            self._transport.cache.invalidate(f"scenes:{scene_id}")

    def resolve(
        self,
        scene_id: str | UUID,
        *,
        variables: dict[str, Any] | None = None,
        caller_system: str | None = None,
    ) -> SceneResolveResult:
        body: dict[str, Any] = {"variables": variables or {}}
        if caller_system is not None:
            body["caller_system"] = caller_system
        data, _ = self._transport.request("POST", f"{_PREFIX}/{scene_id}/resolve", json=body)
        return SceneResolveResult(**data)

    def dependencies(self, scene_id: str | UUID) -> DependencyGraph:
        data, _ = self._transport.request("GET", f"{_PREFIX}/{scene_id}/dependencies")
        return DependencyGraph(**data)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class AsyncScenesResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        name: str,
        slug: str,
        project_id: str | UUID,
        pipeline: dict[str, Any],
        description: str | None = None,
        merge_strategy: str = "concat",
        separator: str = "\n\n",
        output_format: str | None = None,
    ) -> Scene:
        body = _build_create_body(
            name=name,
            slug=slug,
            project_id=project_id,
            pipeline=pipeline,
            description=description,
            merge_strategy=merge_strategy,
            separator=separator,
            output_format=output_format,
        )
        data, _ = await self._transport.request("POST", _PREFIX, json=body)
        return Scene(**data)

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        project_id: str | UUID | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> PaginatedList[Scene]:
        params = _build_list_params(
            page=page,
            page_size=page_size,
            project_id=project_id,
            sort_by=sort_by,
            order=order,
        )
        data, meta = await self._transport.request("GET", _PREFIX, params=params)
        return _paginated_scenes(data, meta)

    async def get(self, scene_id: str | UUID) -> Scene:
        cache = self._transport.cache
        cache_key = f"scenes:{scene_id}"
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        data, _ = await self._transport.request("GET", f"{_PREFIX}/{scene_id}")
        result = Scene(**data)
        if cache:
            cache.set(cache_key, result)
        return result

    async def update(self, scene_id: str | UUID, **kwargs: Any) -> Scene:
        body = _build_update_body(**kwargs)
        data, _ = await self._transport.request("PUT", f"{_PREFIX}/{scene_id}", json=body)
        if self._transport.cache:
            self._transport.cache.invalidate(f"scenes:{scene_id}")
        return Scene(**data)

    async def delete(self, scene_id: str | UUID) -> None:
        await self._transport.request("DELETE", f"{_PREFIX}/{scene_id}")
        if self._transport.cache:
            self._transport.cache.invalidate(f"scenes:{scene_id}")

    async def resolve(
        self,
        scene_id: str | UUID,
        *,
        variables: dict[str, Any] | None = None,
        caller_system: str | None = None,
    ) -> SceneResolveResult:
        body: dict[str, Any] = {"variables": variables or {}}
        if caller_system is not None:
            body["caller_system"] = caller_system
        data, _ = await self._transport.request(
            "POST",
            f"{_PREFIX}/{scene_id}/resolve",
            json=body,
        )
        return SceneResolveResult(**data)

    async def dependencies(self, scene_id: str | UUID) -> DependencyGraph:
        data, _ = await self._transport.request("GET", f"{_PREFIX}/{scene_id}/dependencies")
        return DependencyGraph(**data)
