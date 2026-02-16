"""Thin wrapper around openai.AsyncOpenAI for unified LLM calls."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import structlog
from openai import APIError, AsyncOpenAI

from app.config import settings
from app.core.exceptions import LLMError

logger = structlog.get_logger()


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kwargs: dict = {"api_key": settings.OPENAI_API_KEY, "timeout": settings.LLM_TIMEOUT}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        _client = AsyncOpenAI(**kwargs)
    return _client


def reset_client() -> None:
    """Reset the cached client (useful for tests)."""
    global _client
    _client = None


async def complete(
    prompt: str,
    *,
    model: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> LLMResponse:
    """Call the LLM and return a structured response."""
    client = _get_client()
    model = model or settings.LLM_DEFAULT_MODEL
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    start = time.monotonic()
    try:
        resp = await client.chat.completions.create(**kwargs)
    except APIError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.error("llm_call_failed", model=model, elapsed_ms=elapsed_ms, error=str(exc))
        raise LLMError(
            message="LLM service unavailable",
            detail=f"{exc.__class__.__name__}: {exc.message}",
        ) from exc
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.error("llm_call_failed", model=model, elapsed_ms=elapsed_ms, error=str(exc))
        raise LLMError(
            message="LLM service unavailable",
            detail=str(exc),
        ) from exc

    elapsed_ms = int((time.monotonic() - start) * 1000)
    content = resp.choices[0].message.content or ""
    usage_info = {}
    if resp.usage:
        usage_info = {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
        }

    logger.info(
        "llm_call",
        model=model,
        elapsed_ms=elapsed_ms,
        prompt_tokens=usage_info.get("prompt_tokens"),
        completion_tokens=usage_info.get("completion_tokens"),
    )

    return LLMResponse(content=content, model=resp.model, usage=usage_info)
