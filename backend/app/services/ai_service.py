"""AI optimization service — generate, enhance, variants, evaluate, lint (Phase 5)."""

from __future__ import annotations

import asyncio
import json
import re
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import LLMError, ValidationError
from app.models.call_log import CallLog
from app.schemas.ai import (
    EnhanceRequest,
    EnhanceResponse,
    EvaluateBatchRequest,
    EvaluateBatchResponse,
    EvaluateItemResult,
    EvaluateRequest,
    EvaluateResponse,
    GenerateCandidate,
    GenerateRequest,
    GenerateResponse,
    LintIssue,
    LintRequest,
    LintResponse,
    VariantCandidate,
    VariantRequest,
    VariantResponse,
)
from app.schemas.prompt import PromptCreate
from app.services import llm_client, prompt_service

logger = structlog.get_logger()


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Strip markdown fences if present
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*\n?", "", stripped)
        stripped = re.sub(r"\n?```\s*$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise LLMError(
            message="Failed to parse LLM response",
            detail=f"Invalid JSON from LLM: {exc}",
        ) from exc


async def _log_call(
    db: AsyncSession,
    *,
    caller_system: str,
    rendered_content: str | None = None,
    token_count: int | None = None,
    response_time_ms: int | None = None,
    quality_score: float | None = None,
    prompt_id: uuid.UUID | None = None,
) -> None:
    """Write an entry to call_logs."""
    log = CallLog(
        prompt_id=prompt_id,
        caller_system=caller_system,
        rendered_content=rendered_content,
        token_count=token_count,
        response_time_ms=response_time_ms,
        quality_score=quality_score,
    )
    db.add(log)
    await db.flush()


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

_GENERATE_SYSTEM = """\
You are an expert prompt engineer. Generate high-quality prompt candidates.
Return a JSON object with this exact structure:
{
  "candidates": [
    {
      "content": "the full prompt text",
      "name": "descriptive name for this prompt",
      "slug": "kebab-case-slug",
      "variables": [{"name": "var_name", "type": "string", "required": true, "description": "..."}],
      "rationale": "why this prompt design works"
    }
  ]
}
"""


async def generate_prompts(
    db: AsyncSession,
    request: GenerateRequest,
    user_id: uuid.UUID | None = None,
) -> GenerateResponse:
    if request.auto_save and request.project_id is None:
        raise ValidationError(
            message="project_id required when auto_save is true",
            detail="Set project_id to specify where to save generated prompts",
        )

    user_prompt = (
        f"Generate {request.count} prompt candidates.\n"
        f"Description: {request.description}\n"
        f"Target format: {request.target_format}\n"
        f"Language: {request.language}\n"
    )

    resp = await llm_client.complete(
        user_prompt,
        system=_GENERATE_SYSTEM,
        response_format={"type": "json_object"},
    )

    parsed = _parse_json(resp.content)
    candidates = [GenerateCandidate(**c) for c in parsed.get("candidates", [])]

    token_count = resp.usage.get("prompt_tokens", 0) + resp.usage.get("completion_tokens", 0)
    await _log_call(db, caller_system="ai_generate", token_count=token_count)

    saved_ids: list[uuid.UUID] | None = None
    if request.auto_save and request.project_id:
        saved_ids = []
        for candidate in candidates:
            create_data = PromptCreate(
                name=candidate.name,
                slug=candidate.slug,
                content=candidate.content,
                project_id=request.project_id,
                variables=candidate.variables,  # type: ignore[arg-type]
            )
            prompt = await prompt_service.create_prompt(db, create_data, created_by=user_id)
            saved_ids.append(prompt.id)

    return GenerateResponse(
        candidates=candidates,
        model_used=resp.model,
        saved_prompt_ids=saved_ids,
    )


# ---------------------------------------------------------------------------
# Enhance
# ---------------------------------------------------------------------------

_ENHANCE_SYSTEM = """You are an expert prompt engineer. Analyze and improve the given prompt.
Return a JSON object with this exact structure:
{
  "enhanced_content": "the improved prompt text",
  "improvements": ["description of improvement 1", "description of improvement 2"]
}
"""


async def enhance_prompt(
    db: AsyncSession,
    request: EnhanceRequest,
    user_id: uuid.UUID | None = None,
) -> EnhanceResponse:
    user_prompt = (
        f"Improve this prompt focusing on these aspects: {', '.join(request.aspects)}\n"
        f"Language: {request.language}\n\n"
        f"Original prompt:\n{request.content}"
    )

    resp = await llm_client.complete(
        user_prompt,
        system=_ENHANCE_SYSTEM,
        response_format={"type": "json_object"},
    )

    parsed = _parse_json(resp.content)
    token_count = resp.usage.get("prompt_tokens", 0) + resp.usage.get("completion_tokens", 0)
    await _log_call(db, caller_system="ai_enhance", token_count=token_count)

    return EnhanceResponse(
        original_content=request.content,
        enhanced_content=parsed.get("enhanced_content", ""),
        improvements=parsed.get("improvements", []),
        model_used=resp.model,
    )


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------

_VARIANT_SYSTEM = """\
You are an expert prompt engineer. Generate variants of the given prompt.
Return a JSON object with this exact structure:
{
  "variants": [
    {
      "variant_type": "concise",
      "content": "the variant prompt text",
      "description": "what makes this variant different"
    }
  ]
}
"""


async def generate_variants(
    db: AsyncSession,
    request: VariantRequest,
    user_id: uuid.UUID | None = None,
) -> VariantResponse:
    user_prompt = (
        f"Generate {request.count} variants of types: {', '.join(request.variant_types)}\n"
        f"Language: {request.language}\n\n"
        f"Original prompt:\n{request.content}"
    )

    resp = await llm_client.complete(
        user_prompt,
        system=_VARIANT_SYSTEM,
        response_format={"type": "json_object"},
    )

    parsed = _parse_json(resp.content)
    variants = [VariantCandidate(**v) for v in parsed.get("variants", [])]

    token_count = resp.usage.get("prompt_tokens", 0) + resp.usage.get("completion_tokens", 0)
    await _log_call(db, caller_system="ai_variants", token_count=token_count)

    return VariantResponse(variants=variants, model_used=resp.model)


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

_EVALUATE_SYSTEM = """You are an expert prompt evaluator. Score the given prompt on each criterion from 0 to 5.
Return a JSON object with this exact structure:
{
  "overall_score": 3.5,
  "criteria_scores": {"clarity": 4.0, "specificity": 3.0},
  "suggestions": ["suggestion 1", "suggestion 2"]
}
"""


async def _evaluate_single(content: str, criteria: list[str]) -> dict:
    """Evaluate a single prompt and return raw parsed dict."""
    user_prompt = f"Evaluate this prompt on criteria: {', '.join(criteria)}\n\nPrompt:\n{content}"

    resp = await llm_client.complete(
        user_prompt,
        system=_EVALUATE_SYSTEM,
        response_format={"type": "json_object"},
    )

    parsed = _parse_json(resp.content)
    parsed["_model"] = resp.model
    parsed["_usage"] = resp.usage
    return parsed


async def evaluate_prompt(
    db: AsyncSession,
    request: EvaluateRequest,
    user_id: uuid.UUID | None = None,
) -> EvaluateResponse:
    parsed = await _evaluate_single(request.content, request.criteria)

    token_count = parsed["_usage"].get("prompt_tokens", 0) + parsed["_usage"].get("completion_tokens", 0)
    quality_score = parsed.get("overall_score", 0.0)
    await _log_call(
        db, caller_system="ai_evaluate", token_count=token_count, quality_score=quality_score,
    )

    return EvaluateResponse(
        overall_score=parsed.get("overall_score", 0.0),
        criteria_scores=parsed.get("criteria_scores", {}),
        suggestions=parsed.get("suggestions", []),
        model_used=parsed["_model"],
    )


async def evaluate_batch(
    db: AsyncSession,
    request: EvaluateBatchRequest,
    user_id: uuid.UUID | None = None,
) -> EvaluateBatchResponse:
    semaphore = asyncio.Semaphore(settings.LLM_BATCH_CONCURRENCY)
    last_model: list[str] = [settings.LLM_DEFAULT_MODEL]

    async def _eval_one(prompt_id: uuid.UUID) -> EvaluateItemResult:
        async with semaphore:
            prompt = await prompt_service.get_prompt(db, prompt_id)
            try:
                parsed = await _evaluate_single(prompt.content, request.criteria)
                last_model[0] = parsed.get("_model", last_model[0])
                return EvaluateItemResult(
                    prompt_id=prompt_id,
                    overall_score=parsed.get("overall_score", 0.0),
                    criteria_scores=parsed.get("criteria_scores", {}),
                    suggestions=parsed.get("suggestions", []),
                )
            except LLMError as exc:
                return EvaluateItemResult(
                    prompt_id=prompt_id,
                    overall_score=0.0,
                    criteria_scores={},
                    suggestions=[],
                    error=exc.message,
                )

    tasks = [_eval_one(pid) for pid in request.prompt_ids]
    results = await asyncio.gather(*tasks)

    await _log_call(db, caller_system="ai_evaluate_batch")

    return EvaluateBatchResponse(results=list(results), model_used=last_model[0])


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

_LINT_SYSTEM = """You are a prompt linting expert. Analyze the prompt for anti-patterns and quality issues.
Return a JSON object with this exact structure:
{
  "issues": [
    {
      "severity": "warning",
      "rule": "redundant",
      "message": "description of the issue",
      "suggestion": "how to fix it"
    }
  ]
}
Only return issues you actually find. Possible rules: redundant, contradictory, vague, ambiguous.
"""

# Thresholds for local lint rules
_MAX_CONTENT_LENGTH = 2000


def _lint_local(content: str, variables: list[dict] | None) -> list[LintIssue]:
    """Run local (non-LLM) lint rules."""
    issues: list[LintIssue] = []

    # too_long
    if len(content) > _MAX_CONTENT_LENGTH:
        issues.append(
            LintIssue(
                severity="warning",
                rule="too_long",
                message=f"Prompt is {len(content)} characters, exceeding the {_MAX_CONTENT_LENGTH} character guideline",
                suggestion="Consider breaking the prompt into smaller, composable parts",
            )
        )

    if variables is not None:
        # Find template variables used in content (Jinja2 style)
        used_vars = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", content))
        defined_vars = {v.get("name", "") for v in variables if v.get("name")}

        # unused_variable — defined but not referenced
        for var_name in defined_vars - used_vars:
            issues.append(
                LintIssue(
                    severity="warning",
                    rule="unused_variable",
                    message=f"Variable '{var_name}' is defined but not used in the prompt content",
                    suggestion=f"Remove '{var_name}' from variables or reference it with {{{{ {var_name} }}}}",
                )
            )

        # undefined_variable — referenced but not defined
        for var_name in used_vars - defined_vars:
            issues.append(
                LintIssue(
                    severity="error",
                    rule="undefined_variable",
                    message=f"Variable '{var_name}' is used in the prompt but not defined in variables",
                    suggestion=f"Add '{var_name}' to the variables list",
                )
            )

    return issues


async def lint_prompt(
    db: AsyncSession,
    request: LintRequest,
    user_id: uuid.UUID | None = None,
) -> LintResponse:
    issues = _lint_local(request.content, request.variables)

    # Try LLM-based lint (optional — gracefully degrade if LLM unavailable)
    try:
        resp = await llm_client.complete(
            f"Lint this prompt:\n{request.content}",
            system=_LINT_SYSTEM,
            response_format={"type": "json_object"},
        )
        parsed = _parse_json(resp.content)
        for issue_data in parsed.get("issues", []):
            issues.append(LintIssue(**issue_data))
        await _log_call(db, caller_system="ai_lint")
    except LLMError:
        logger.warning("lint_llm_unavailable", msg="LLM unavailable, returning local lint only")

    # Compute score: start at 100, deduct for issues
    score = 100.0
    for issue in issues:
        if issue.severity == "error":
            score -= 20
        elif issue.severity == "warning":
            score -= 10
        else:
            score -= 5
    score = max(0.0, score)

    return LintResponse(issues=issues, score=score)
