"""Pydantic schemas for AI optimization endpoints (Phase 5)."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    description: str
    target_format: str = "text"
    language: str = "zh"
    count: int = Field(default=3, ge=1, le=5)
    auto_save: bool = False
    project_id: uuid.UUID | None = None


class GenerateCandidate(BaseModel):
    content: str
    name: str
    slug: str
    variables: list[dict[str, Any]] = []
    rationale: str


class GenerateResponse(BaseModel):
    candidates: list[GenerateCandidate]
    model_used: str
    saved_prompt_ids: list[uuid.UUID] | None = None


# ---------------------------------------------------------------------------
# Enhance
# ---------------------------------------------------------------------------


class EnhanceRequest(BaseModel):
    content: str = Field(..., min_length=1)
    aspects: list[str] = ["clarity", "specificity", "structure"]
    language: str = "zh"


class EnhanceResponse(BaseModel):
    original_content: str
    enhanced_content: str
    improvements: list[str]
    model_used: str


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class VariantRequest(BaseModel):
    content: str = Field(..., min_length=1)
    variant_types: list[str] = ["concise", "detailed", "creative"]
    count: int = Field(default=3, ge=1, le=5)
    language: str = "zh"


class VariantCandidate(BaseModel):
    variant_type: str
    content: str
    description: str


class VariantResponse(BaseModel):
    variants: list[VariantCandidate]
    model_used: str


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------


class EvaluateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    criteria: list[str] = ["clarity", "specificity", "completeness", "consistency"]


class EvaluateResponse(BaseModel):
    overall_score: float
    criteria_scores: dict[str, float]
    suggestions: list[str]
    model_used: str


class EvaluateItemResult(BaseModel):
    prompt_id: uuid.UUID
    overall_score: float
    criteria_scores: dict[str, float]
    suggestions: list[str]
    error: str | None = None


class EvaluateBatchRequest(BaseModel):
    prompt_ids: list[uuid.UUID] = Field(..., max_length=10)
    criteria: list[str] = ["clarity", "specificity", "completeness", "consistency"]


class EvaluateBatchResponse(BaseModel):
    results: list[EvaluateItemResult]
    model_used: str


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------


class LintRequest(BaseModel):
    content: str = Field(..., min_length=1)
    variables: list[dict[str, Any]] | None = None


class LintIssue(BaseModel):
    severity: str  # "error" | "warning" | "info"
    rule: str
    message: str
    suggestion: str | None = None


class LintResponse(BaseModel):
    issues: list[LintIssue]
    score: float
