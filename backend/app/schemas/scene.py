import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ConditionOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"


class StepCondition(BaseModel):
    variable: str
    operator: ConditionOperator
    value: Any = None


class PromptReference(BaseModel):
    prompt_id: uuid.UUID
    version: str | None = None


class PipelineStep(BaseModel):
    id: str
    prompt_ref: PromptReference
    variables: dict[str, Any] = {}
    condition: StepCondition | None = None
    output_key: str | None = None


class PipelineConfig(BaseModel):
    steps: list[PipelineStep]

    @model_validator(mode="after")
    def validate_unique_step_ids(self) -> "PipelineConfig":
        ids = [step.id for step in self.steps]
        if len(ids) != len(set(ids)):
            duplicates = [sid for sid in ids if ids.count(sid) > 1]
            raise ValueError(f"Duplicate step ids: {set(duplicates)}")
        return self


VALID_MERGE_STRATEGIES = {"concat", "chain", "select_best"}


class SceneCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    project_id: uuid.UUID
    pipeline: PipelineConfig
    merge_strategy: str = "concat"
    separator: str = "\n\n"
    output_format: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("slug must be kebab-case (lowercase letters, numbers, hyphens)")
        return v

    @field_validator("merge_strategy")
    @classmethod
    def validate_merge_strategy(cls, v: str) -> str:
        if v not in VALID_MERGE_STRATEGIES:
            raise ValueError(f"merge_strategy must be one of: {sorted(VALID_MERGE_STRATEGIES)}")
        return v


class SceneUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    pipeline: PipelineConfig | None = None
    merge_strategy: str | None = None
    separator: str | None = None
    output_format: str | None = None

    @field_validator("merge_strategy")
    @classmethod
    def validate_merge_strategy(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_MERGE_STRATEGIES:
            raise ValueError(f"merge_strategy must be one of: {sorted(VALID_MERGE_STRATEGIES)}")
        return v


class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    project_id: uuid.UUID
    pipeline: dict
    merge_strategy: str
    separator: str
    output_format: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SceneResolveRequest(BaseModel):
    variables: dict[str, Any] = {}
    caller_system: str | None = None


class StepResult(BaseModel):
    step_id: str
    prompt_id: uuid.UUID
    prompt_name: str
    version: str
    rendered_content: str
    skipped: bool = False
    skip_reason: str | None = None


class SceneResolveResponse(BaseModel):
    scene_id: uuid.UUID
    scene_name: str
    merge_strategy: str
    final_content: str
    steps: list[StepResult]
    total_token_estimate: int


class DependencyNode(BaseModel):
    id: uuid.UUID
    name: str
    project_id: uuid.UUID
    version: str
    is_shared: bool


class DependencyEdge(BaseModel):
    source: uuid.UUID
    target: uuid.UUID
    step_id: str | None = None
    ref_type: str


class DependencyGraph(BaseModel):
    nodes: list[DependencyNode]
    edges: list[DependencyEdge]
