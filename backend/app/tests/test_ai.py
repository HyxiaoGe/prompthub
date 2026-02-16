"""Tests for AI optimization endpoints (Phase 5).

All LLM calls are mocked — no real API key needed.
"""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_log import CallLog
from app.models.project import Project
from app.models.prompt import Prompt
from app.services.llm_client import LLMResponse

API = "/api/v1/ai"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_llm_response(content_dict: dict, model: str = "gpt-4o-mini") -> LLMResponse:
    return LLMResponse(
        content=json.dumps(content_dict),
        model=model,
        usage={"prompt_tokens": 100, "completion_tokens": 50},
    )


async def _create_project(db: AsyncSession, user_id: uuid.UUID) -> Project:
    project = Project(
        name="AI Test Project",
        slug=f"ai-test-{uuid.uuid4().hex[:8]}",
        description="Project for AI tests",
        created_by=user_id,
    )
    db.add(project)
    await db.flush()
    return project


async def _create_prompt(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> Prompt:
    prompt = Prompt(
        name="Test Prompt",
        slug=f"test-{uuid.uuid4().hex[:8]}",
        content="You are a helpful assistant. Summarize the {{ topic }} document.",
        project_id=project_id,
        variables=[{"name": "topic", "type": "string", "required": True}],
        created_by=user_id,
    )
    db.add(prompt)
    await db.flush()
    return prompt


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------


class TestGenerate:
    @pytest.mark.asyncio
    async def test_generate_success(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "candidates": [
                {
                    "content": "You are an audio summarizer...",
                    "name": "Audio Summarizer",
                    "slug": "audio-summarizer",
                    "variables": [{"name": "audio_url", "type": "string", "required": True}],
                    "rationale": "Clear system prompt for audio summarization",
                },
                {
                    "content": "Summarize the following audio...",
                    "name": "Audio Summary V2",
                    "slug": "audio-summary-v2",
                    "variables": [],
                    "rationale": "Simpler variant",
                },
            ]
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/generate", json={
                "description": "Generate an audio summarization prompt",
                "count": 2,
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["candidates"]) == 2
        assert data["candidates"][0]["name"] == "Audio Summarizer"
        assert data["model_used"] == "gpt-4o-mini"
        assert data["saved_prompt_ids"] is None

    @pytest.mark.asyncio
    async def test_generate_auto_save(self, client: AsyncClient, db_session: AsyncSession, test_user) -> None:
        project = await _create_project(db_session, test_user.id)

        mock_resp = _mock_llm_response({
            "candidates": [
                {
                    "content": "Saved prompt content",
                    "name": "Saved Prompt",
                    "slug": f"saved-{uuid.uuid4().hex[:8]}",
                    "variables": [],
                    "rationale": "Auto-saved prompt",
                },
            ]
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/generate", json={
                "description": "Test auto save",
                "count": 1,
                "auto_save": True,
                "project_id": str(project.id),
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["saved_prompt_ids"] is not None
        assert len(data["saved_prompt_ids"]) == 1

    @pytest.mark.asyncio
    async def test_generate_auto_save_no_project_id(self, client: AsyncClient) -> None:
        resp = await client.post(f"{API}/generate", json={
            "description": "Test auto save",
            "auto_save": True,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_count_validation(self, client: AsyncClient) -> None:
        resp = await client.post(f"{API}/generate", json={
            "description": "Test",
            "count": 10,
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Enhance
# ---------------------------------------------------------------------------


class TestEnhance:
    @pytest.mark.asyncio
    async def test_enhance_success(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "enhanced_content": "Improved: You are an expert assistant...",
            "improvements": ["Added role specification", "Improved clarity"],
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/enhance", json={
                "content": "You are a helper.",
                "aspects": ["clarity", "specificity"],
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["original_content"] == "You are a helper."
        assert "Improved" in data["enhanced_content"]
        assert len(data["improvements"]) == 2

    @pytest.mark.asyncio
    async def test_enhance_empty_content(self, client: AsyncClient) -> None:
        resp = await client.post(f"{API}/enhance", json={"content": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class TestVariants:
    @pytest.mark.asyncio
    async def test_variants_success(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "variants": [
                {"variant_type": "concise", "content": "Be brief...", "description": "Shortened version"},
                {"variant_type": "detailed", "content": "Be thorough...", "description": "Expanded version"},
                {"variant_type": "creative", "content": "Be creative...", "description": "Creative version"},
            ]
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/variants", json={
                "content": "You are a helpful assistant.",
                "variant_types": ["concise", "detailed", "creative"],
                "count": 3,
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["variants"]) == 3
        assert data["variants"][0]["variant_type"] == "concise"

    @pytest.mark.asyncio
    async def test_variants_custom_types(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "variants": [
                {"variant_type": "formal", "content": "Formal prompt...", "description": "Formal style"},
            ]
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/variants", json={
                "content": "You are a helper.",
                "variant_types": ["formal"],
                "count": 1,
            })

        assert resp.status_code == 200
        assert len(resp.json()["data"]["variants"]) == 1


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------


class TestEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_success(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "overall_score": 3.8,
            "criteria_scores": {"clarity": 4.0, "specificity": 3.5, "completeness": 4.0, "consistency": 3.5},
            "suggestions": ["Add more context", "Be more specific about output format"],
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/evaluate", json={
                "content": "You are a helpful assistant.",
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert 0 <= data["overall_score"] <= 5
        assert "clarity" in data["criteria_scores"]
        assert len(data["suggestions"]) >= 1

    @pytest.mark.asyncio
    async def test_evaluate_batch_success(
        self, client: AsyncClient, db_session: AsyncSession, test_user,
    ) -> None:
        project = await _create_project(db_session, test_user.id)
        prompt1 = await _create_prompt(db_session, project.id, test_user.id)
        prompt2 = await _create_prompt(db_session, project.id, test_user.id)

        mock_resp = _mock_llm_response({
            "overall_score": 4.0,
            "criteria_scores": {"clarity": 4.5, "specificity": 3.5},
            "suggestions": ["Good prompt"],
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/evaluate/batch", json={
                "prompt_ids": [str(prompt1.id), str(prompt2.id)],
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["results"]) == 2
        assert data["results"][0]["prompt_id"] == str(prompt1.id)
        assert data["results"][0]["overall_score"] == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_batch_too_many(self, client: AsyncClient) -> None:
        ids = [str(uuid.uuid4()) for _ in range(11)]
        resp = await client.post(f"{API}/evaluate/batch", json={"prompt_ids": ids})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_evaluate_batch_not_found(
        self, client: AsyncClient, db_session: AsyncSession, test_user,
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"{API}/evaluate/batch", json={
            "prompt_ids": [fake_id],
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------


class TestLint:
    @pytest.mark.asyncio
    async def test_lint_too_long(self, client: AsyncClient) -> None:
        long_content = "x" * 2500

        # Mock LLM returns no additional issues
        mock_resp = _mock_llm_response({"issues": []})
        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/lint", json={"content": long_content})

        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = [i["rule"] for i in data["issues"]]
        assert "too_long" in rules

    @pytest.mark.asyncio
    async def test_lint_unused_variable(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({"issues": []})
        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/lint", json={
                "content": "Hello {{ name }}",
                "variables": [
                    {"name": "name", "type": "string"},
                    {"name": "unused_var", "type": "string"},
                ],
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = [i["rule"] for i in data["issues"]]
        assert "unused_variable" in rules

    @pytest.mark.asyncio
    async def test_lint_undefined_variable(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({"issues": []})
        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/lint", json={
                "content": "Hello {{ name }} and {{ missing_var }}",
                "variables": [{"name": "name", "type": "string"}],
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = [i["rule"] for i in data["issues"]]
        assert "undefined_variable" in rules

    @pytest.mark.asyncio
    async def test_lint_with_llm_issues(self, client: AsyncClient) -> None:
        mock_resp = _mock_llm_response({
            "issues": [
                {
                    "severity": "warning",
                    "rule": "redundant",
                    "message": "Redundant instruction found",
                    "suggestion": "Remove duplicate instructions",
                },
                {
                    "severity": "info",
                    "rule": "vague",
                    "message": "Prompt is too vague",
                    "suggestion": "Add more specific instructions",
                },
            ]
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/lint", json={
                "content": "Do stuff. Do stuff again.",
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = [i["rule"] for i in data["issues"]]
        assert "redundant" in rules
        assert "vague" in rules
        assert data["score"] < 100

    @pytest.mark.asyncio
    async def test_lint_no_variables(self, client: AsyncClient) -> None:
        """Lint without variables should still work (local rules skip variable checks)."""
        mock_resp = _mock_llm_response({"issues": []})
        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/lint", json={"content": "Short prompt."})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["score"] == 100

    @pytest.mark.asyncio
    async def test_lint_llm_unavailable_graceful(self, client: AsyncClient) -> None:
        """When LLM is unavailable, lint should still return local results."""
        from app.core.exceptions import LLMError

        with patch(
            "app.services.ai_service.llm_client.complete",
            new_callable=AsyncMock,
            side_effect=LLMError("LLM down"),
        ):
            resp = await client.post(f"{API}/lint", json={
                "content": "x" * 2500,
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = [i["rule"] for i in data["issues"]]
        assert "too_long" in rules


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_llm_timeout_returns_502(self, client: AsyncClient) -> None:
        from app.core.exceptions import LLMError

        with patch(
            "app.services.ai_service.llm_client.complete",
            new_callable=AsyncMock,
            side_effect=LLMError("LLM service unavailable", detail="Timeout"),
        ):
            resp = await client.post(f"{API}/evaluate", json={"content": "Test prompt."})

        assert resp.status_code == 502

    @pytest.mark.asyncio
    async def test_invalid_request_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(f"{API}/generate", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestAuth:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_401(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.post(f"{API}/generate", json={"description": "test"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Call log
# ---------------------------------------------------------------------------


class TestCallLog:
    @pytest.mark.asyncio
    async def test_ai_call_logged(self, client: AsyncClient, db_session: AsyncSession) -> None:
        mock_resp = _mock_llm_response({
            "overall_score": 4.0,
            "criteria_scores": {"clarity": 4.0},
            "suggestions": [],
        })

        with patch("app.services.ai_service.llm_client.complete", new_callable=AsyncMock, return_value=mock_resp):
            resp = await client.post(f"{API}/evaluate", json={"content": "Test prompt."})

        assert resp.status_code == 200

        result = await db_session.execute(
            select(CallLog).where(CallLog.caller_system == "ai_evaluate")
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.quality_score == 4.0
