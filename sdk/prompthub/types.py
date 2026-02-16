"""PromptHub SDK response types — mirrors backend Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


class Prompt(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    content: str
    format: str
    template_engine: str
    variables: Any = None
    tags: list[str] | None = None
    category: str | None = None
    project_id: UUID
    is_shared: bool
    current_version: str
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class PromptSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    format: str
    tags: list[str] | None = None
    category: str | None = None
    project_id: UUID
    is_shared: bool
    current_version: str
    created_at: datetime
    updated_at: datetime


class RenderResult(BaseModel):
    prompt_id: UUID
    version: str
    rendered_content: str
    variables_used: dict[str, Any]


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------


class Version(BaseModel):
    id: UUID
    prompt_id: UUID
    version: str
    content: str
    variables: Any = None
    changelog: str | None = None
    status: str
    created_by: UUID | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class Project(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(Project):
    prompt_count: int = 0
    scene_count: int = 0


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


class Scene(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    project_id: UUID
    pipeline: dict[str, Any]
    merge_strategy: str
    separator: str
    output_format: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class StepResult(BaseModel):
    step_id: str
    prompt_id: UUID
    prompt_name: str
    version: str
    rendered_content: str
    skipped: bool = False
    skip_reason: str | None = None


class SceneResolveResult(BaseModel):
    scene_id: UUID
    scene_name: str
    merge_strategy: str
    final_content: str
    steps: list[StepResult]
    total_token_estimate: int


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


class DependencyNode(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    version: str
    is_shared: bool


class DependencyEdge(BaseModel):
    source: UUID
    target: UUID
    step_id: str | None = None
    ref_type: str


class DependencyGraph(BaseModel):
    nodes: list[DependencyNode]
    edges: list[DependencyEdge]


# ---------------------------------------------------------------------------
# AI (Phase 5)
# ---------------------------------------------------------------------------


class GenerateCandidate(BaseModel):
    content: str
    name: str
    slug: str
    variables: list[dict[str, Any]] = []
    rationale: str


class GenerateResult(BaseModel):
    candidates: list[GenerateCandidate]
    model_used: str
    saved_prompt_ids: list[UUID] | None = None


class EnhanceResult(BaseModel):
    original_content: str
    enhanced_content: str
    improvements: list[str]
    model_used: str


class VariantCandidate(BaseModel):
    variant_type: str
    content: str
    description: str


class VariantResult(BaseModel):
    variants: list[VariantCandidate]
    model_used: str


class EvaluateResult(BaseModel):
    overall_score: float
    criteria_scores: dict[str, float]
    suggestions: list[str]
    model_used: str


class EvaluateItemResult(BaseModel):
    prompt_id: UUID
    overall_score: float
    criteria_scores: dict[str, float]
    suggestions: list[str]
    error: str | None = None


class EvaluateBatchResult(BaseModel):
    results: list[EvaluateItemResult]
    model_used: str


class LintIssue(BaseModel):
    severity: str
    rule: str
    message: str
    suggestion: str | None = None


class LintResult(BaseModel):
    issues: list[LintIssue]
    score: float
