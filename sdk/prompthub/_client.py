"""Top-level client classes — sync and async."""

from __future__ import annotations

from types import TracebackType

from prompthub._base import AsyncTransport, SyncTransport
from prompthub.resources.ai import AIResource, AsyncAIResource
from prompthub.resources.projects import AsyncProjectsResource, ProjectsResource
from prompthub.resources.prompts import AsyncPromptsResource, PromptsResource
from prompthub.resources.scenes import AsyncScenesResource, ScenesResource
from prompthub.resources.shared import AsyncSharedResource, SharedResource


class PromptHubClient:
    """Synchronous PromptHub client.

    Usage::

        client = PromptHubClient(base_url="http://localhost:8000", api_key="ph-xxx")
        prompt = client.prompts.get_by_slug("summary-zh")
        client.close()

    Or as a context manager::

        with PromptHubClient(...) as client:
            result = client.scenes.resolve(scene_id, variables={...})
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        cache_ttl: int | None = None,
    ) -> None:
        self._transport = SyncTransport(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            cache_ttl=cache_ttl,
        )
        self.prompts = PromptsResource(self._transport)
        self.scenes = ScenesResource(self._transport)
        self.projects = ProjectsResource(self._transport)
        self.shared = SharedResource(self._transport)
        self.ai = AIResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> PromptHubClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncPromptHubClient:
    """Asynchronous PromptHub client.

    Usage::

        async with AsyncPromptHubClient(...) as client:
            result = await client.scenes.resolve(scene_id, variables={...})
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        cache_ttl: int | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            cache_ttl=cache_ttl,
        )
        self.prompts = AsyncPromptsResource(self._transport)
        self.scenes = AsyncScenesResource(self._transport)
        self.projects = AsyncProjectsResource(self._transport)
        self.shared = AsyncSharedResource(self._transport)
        self.ai = AsyncAIResource(self._transport)

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> AsyncPromptHubClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
