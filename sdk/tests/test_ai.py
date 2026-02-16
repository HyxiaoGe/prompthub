"""Tests for SDK AI resource — sync and async."""

from __future__ import annotations

import pytest

from prompthub import (
    AsyncPromptHubClient,
    EnhanceResult,
    EvaluateBatchResult,
    EvaluateResult,
    GenerateResult,
    LintResult,
    LLMError,
    PromptHubClient,
    VariantResult,
)
from tests.conftest import PROMPT_ID, envelope, error_envelope

# ---------------------------------------------------------------------------
# Mock response data
# ---------------------------------------------------------------------------

GENERATE_DATA = {
    "candidates": [
        {
            "content": "You are an audio summarizer.",
            "name": "Audio Summarizer",
            "slug": "audio-summarizer",
            "variables": [{"name": "audio_url", "type": "string", "required": True}],
            "rationale": "Structured prompt for audio summarization",
        }
    ],
    "model_used": "gpt-4o-mini",
    "saved_prompt_ids": None,
}

ENHANCE_DATA = {
    "original_content": "Be helpful.",
    "enhanced_content": "You are a helpful assistant that provides clear, concise answers.",
    "improvements": ["Added role specification", "Improved clarity"],
    "model_used": "gpt-4o-mini",
}

VARIANT_DATA = {
    "variants": [
        {"variant_type": "concise", "content": "Be brief.", "description": "Short version"},
        {"variant_type": "detailed", "content": "Be thorough.", "description": "Long version"},
    ],
    "model_used": "gpt-4o-mini",
}

EVALUATE_DATA = {
    "overall_score": 3.8,
    "criteria_scores": {"clarity": 4.0, "specificity": 3.5},
    "suggestions": ["Be more specific"],
    "model_used": "gpt-4o-mini",
}

EVALUATE_BATCH_DATA = {
    "results": [
        {
            "prompt_id": PROMPT_ID,
            "overall_score": 4.0,
            "criteria_scores": {"clarity": 4.5},
            "suggestions": [],
            "error": None,
        }
    ],
    "model_used": "gpt-4o-mini",
}

LINT_DATA = {
    "issues": [
        {
            "severity": "warning",
            "rule": "too_long",
            "message": "Prompt is too long",
            "suggestion": "Shorten it",
        }
    ],
    "score": 90.0,
}


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestAIResourceSync:
    def test_generate(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/generate", envelope(GENERATE_DATA))
        result = sync_client.ai.generate("audio summarization prompt", count=1)
        assert isinstance(result, GenerateResult)
        assert len(result.candidates) == 1
        assert result.candidates[0].name == "Audio Summarizer"
        assert result.model_used == "gpt-4o-mini"

    def test_enhance(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/enhance", envelope(ENHANCE_DATA))
        result = sync_client.ai.enhance("Be helpful.", aspects=["clarity"])
        assert isinstance(result, EnhanceResult)
        assert result.original_content == "Be helpful."
        assert len(result.improvements) == 2

    def test_variants(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/variants", envelope(VARIANT_DATA))
        result = sync_client.ai.variants("Test prompt", count=2)
        assert isinstance(result, VariantResult)
        assert len(result.variants) == 2
        assert result.variants[0].variant_type == "concise"

    def test_evaluate(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/evaluate", envelope(EVALUATE_DATA))
        result = sync_client.ai.evaluate("Test prompt")
        assert isinstance(result, EvaluateResult)
        assert 0 <= result.overall_score <= 5
        assert "clarity" in result.criteria_scores

    def test_evaluate_batch(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/evaluate/batch", envelope(EVALUATE_BATCH_DATA))
        result = sync_client.ai.evaluate_batch([PROMPT_ID])
        assert isinstance(result, EvaluateBatchResult)
        assert len(result.results) == 1
        assert str(result.results[0].prompt_id) == PROMPT_ID

    def test_lint(self, routes, sync_client: PromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/lint", envelope(LINT_DATA))
        variables = [{"name": "x", "type": "string"}]
        result = sync_client.ai.lint("A long prompt...", variables=variables)
        assert isinstance(result, LintResult)
        assert len(result.issues) == 1
        assert result.issues[0].rule == "too_long"
        assert result.score == 90.0

    def test_llm_error_mapping(self, routes, sync_client: PromptHubClient) -> None:
        routes.add(
            "POST",
            "/api/v1/ai/evaluate",
            error_envelope(50200, "LLM service unavailable", status_code=502),
        )
        with pytest.raises(LLMError) as exc_info:
            sync_client.ai.evaluate("Test")
        assert exc_info.value.code == 50200


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAIResourceAsync:
    @pytest.mark.asyncio
    async def test_generate(self, routes, async_client: AsyncPromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/generate", envelope(GENERATE_DATA))
        result = await async_client.ai.generate("audio summarization prompt")
        assert isinstance(result, GenerateResult)
        assert len(result.candidates) == 1

    @pytest.mark.asyncio
    async def test_enhance(self, routes, async_client: AsyncPromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/enhance", envelope(ENHANCE_DATA))
        result = await async_client.ai.enhance("Be helpful.")
        assert isinstance(result, EnhanceResult)

    @pytest.mark.asyncio
    async def test_evaluate_batch(self, routes, async_client: AsyncPromptHubClient) -> None:
        routes.add("POST", "/api/v1/ai/evaluate/batch", envelope(EVALUATE_BATCH_DATA))
        result = await async_client.ai.evaluate_batch([PROMPT_ID])
        assert isinstance(result, EvaluateBatchResult)
        assert len(result.results) == 1
