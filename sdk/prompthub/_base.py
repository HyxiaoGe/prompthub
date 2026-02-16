"""HTTP transport layer — sync and async variants with envelope unwrapping."""

from __future__ import annotations

from typing import Any

import httpx

from prompthub._cache import TTLCache
from prompthub.exceptions import ERROR_MAP, PromptHubError


class _BaseTransport:
    """Shared config for both sync and async transports."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        cache_ttl: int | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self.cache: TTLCache | None = TTLCache(ttl=cache_ttl) if cache_ttl else None

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _unwrap(response: httpx.Response) -> tuple[Any, dict[str, Any] | None]:
        """Unwrap the standard API envelope ``{code, message, data, meta}``."""
        data = response.json()
        code = data.get("code", 0)

        if response.status_code >= 400 or code != 0:
            error_code = code if code != 0 else response.status_code * 100
            exc_cls = ERROR_MAP.get(error_code, PromptHubError)
            raise exc_cls(
                code=error_code,
                message=data.get("message", response.reason_phrase or "Unknown error"),
                detail=data.get("detail"),
            )

        return data.get("data"), data.get("meta")


class SyncTransport(_BaseTransport):
    """Synchronous HTTP transport backed by ``httpx.Client``."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        cache_ttl: int | None = None,
    ) -> None:
        super().__init__(base_url, api_key, timeout, cache_ttl)
        self._http = httpx.Client(
            base_url=self._base_url,
            headers=self._headers(),
            timeout=self._timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, Any] | None]:
        response = self._http.request(method, path, json=json, params=params)
        return self._unwrap(response)

    def close(self) -> None:
        self._http.close()


class AsyncTransport(_BaseTransport):
    """Asynchronous HTTP transport backed by ``httpx.AsyncClient``."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        cache_ttl: int | None = None,
    ) -> None:
        super().__init__(base_url, api_key, timeout, cache_ttl)
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers(),
            timeout=self._timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, Any] | None]:
        response = await self._http.request(method, path, json=json, params=params)
        return self._unwrap(response)

    async def close(self) -> None:
        await self._http.aclose()
