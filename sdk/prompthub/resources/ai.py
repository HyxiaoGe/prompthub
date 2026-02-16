"""AI optimization resource — generate, enhance, variants, evaluate, lint."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from prompthub._base import AsyncTransport, SyncTransport
from prompthub.types import (
    EnhanceResult,
    EvaluateBatchResult,
    EvaluateResult,
    GenerateResult,
    LintResult,
    VariantResult,
)

_PREFIX = "/api/v1/ai"


def _build_generate_body(
    description: str,
    *,
    count: int,
    target_format: str,
    language: str,
    auto_save: bool,
    project_id: str | UUID | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "description": description,
        "count": count,
        "target_format": target_format,
        "language": language,
        "auto_save": auto_save,
    }
    if project_id is not None:
        body["project_id"] = str(project_id)
    return body


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


class AIResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def generate(
        self,
        description: str,
        *,
        count: int = 3,
        target_format: str = "text",
        language: str = "zh",
        auto_save: bool = False,
        project_id: str | UUID | None = None,
    ) -> GenerateResult:
        body = _build_generate_body(
            description,
            count=count,
            target_format=target_format,
            language=language,
            auto_save=auto_save,
            project_id=project_id,
        )
        data, _ = self._transport.request("POST", f"{_PREFIX}/generate", json=body)
        return GenerateResult(**data)

    def enhance(
        self,
        content: str,
        *,
        aspects: list[str] | None = None,
        language: str = "zh",
    ) -> EnhanceResult:
        body: dict[str, Any] = {"content": content, "language": language}
        if aspects is not None:
            body["aspects"] = aspects
        data, _ = self._transport.request("POST", f"{_PREFIX}/enhance", json=body)
        return EnhanceResult(**data)

    def variants(
        self,
        content: str,
        *,
        variant_types: list[str] | None = None,
        count: int = 3,
        language: str = "zh",
    ) -> VariantResult:
        body: dict[str, Any] = {"content": content, "count": count, "language": language}
        if variant_types is not None:
            body["variant_types"] = variant_types
        data, _ = self._transport.request("POST", f"{_PREFIX}/variants", json=body)
        return VariantResult(**data)

    def evaluate(
        self,
        content: str,
        *,
        criteria: list[str] | None = None,
    ) -> EvaluateResult:
        body: dict[str, Any] = {"content": content}
        if criteria is not None:
            body["criteria"] = criteria
        data, _ = self._transport.request("POST", f"{_PREFIX}/evaluate", json=body)
        return EvaluateResult(**data)

    def evaluate_batch(
        self,
        prompt_ids: list[str | UUID],
        *,
        criteria: list[str] | None = None,
    ) -> EvaluateBatchResult:
        body: dict[str, Any] = {"prompt_ids": [str(pid) for pid in prompt_ids]}
        if criteria is not None:
            body["criteria"] = criteria
        data, _ = self._transport.request("POST", f"{_PREFIX}/evaluate/batch", json=body)
        return EvaluateBatchResult(**data)

    def lint(
        self,
        content: str,
        *,
        variables: list[dict[str, Any]] | None = None,
    ) -> LintResult:
        body: dict[str, Any] = {"content": content}
        if variables is not None:
            body["variables"] = variables
        data, _ = self._transport.request("POST", f"{_PREFIX}/lint", json=body)
        return LintResult(**data)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class AsyncAIResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def generate(
        self,
        description: str,
        *,
        count: int = 3,
        target_format: str = "text",
        language: str = "zh",
        auto_save: bool = False,
        project_id: str | UUID | None = None,
    ) -> GenerateResult:
        body = _build_generate_body(
            description,
            count=count,
            target_format=target_format,
            language=language,
            auto_save=auto_save,
            project_id=project_id,
        )
        data, _ = await self._transport.request("POST", f"{_PREFIX}/generate", json=body)
        return GenerateResult(**data)

    async def enhance(
        self,
        content: str,
        *,
        aspects: list[str] | None = None,
        language: str = "zh",
    ) -> EnhanceResult:
        body: dict[str, Any] = {"content": content, "language": language}
        if aspects is not None:
            body["aspects"] = aspects
        data, _ = await self._transport.request("POST", f"{_PREFIX}/enhance", json=body)
        return EnhanceResult(**data)

    async def variants(
        self,
        content: str,
        *,
        variant_types: list[str] | None = None,
        count: int = 3,
        language: str = "zh",
    ) -> VariantResult:
        body: dict[str, Any] = {"content": content, "count": count, "language": language}
        if variant_types is not None:
            body["variant_types"] = variant_types
        data, _ = await self._transport.request("POST", f"{_PREFIX}/variants", json=body)
        return VariantResult(**data)

    async def evaluate(
        self,
        content: str,
        *,
        criteria: list[str] | None = None,
    ) -> EvaluateResult:
        body: dict[str, Any] = {"content": content}
        if criteria is not None:
            body["criteria"] = criteria
        data, _ = await self._transport.request("POST", f"{_PREFIX}/evaluate", json=body)
        return EvaluateResult(**data)

    async def evaluate_batch(
        self,
        prompt_ids: list[str | UUID],
        *,
        criteria: list[str] | None = None,
    ) -> EvaluateBatchResult:
        body: dict[str, Any] = {"prompt_ids": [str(pid) for pid in prompt_ids]}
        if criteria is not None:
            body["criteria"] = criteria
        data, _ = await self._transport.request("POST", f"{_PREFIX}/evaluate/batch", json=body)
        return EvaluateBatchResult(**data)

    async def lint(
        self,
        content: str,
        *,
        variables: list[dict[str, Any]] | None = None,
    ) -> LintResult:
        body: dict[str, Any] = {"content": content}
        if variables is not None:
            body["variables"] = variables
        data, _ = await self._transport.request("POST", f"{_PREFIX}/lint", json=body)
        return LintResult(**data)
