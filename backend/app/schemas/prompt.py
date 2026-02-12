import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class VariableDefinition(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    default: Any = None
    description: str | None = None
    enum_values: list[str] | None = None


class PromptCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    content: str
    format: str = "text"
    template_engine: str = "jinja2"
    variables: list[VariableDefinition] = []
    tags: list[str] = []
    category: str | None = None
    project_id: uuid.UUID
    is_shared: bool = False

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("slug must be kebab-case (lowercase letters, numbers, hyphens)")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return [tag.lower().strip() for tag in v if tag.strip()]


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content: str | None = None
    format: str | None = None
    template_engine: str | None = None
    variables: list[VariableDefinition] | None = None
    tags: list[str] | None = None
    category: str | None = None
    is_shared: bool | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [tag.lower().strip() for tag in v if tag.strip()]


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    content: str
    format: str
    template_engine: str
    variables: Any
    tags: list[str] | None
    category: str | None
    project_id: uuid.UUID
    is_shared: bool
    current_version: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PromptSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    format: str
    tags: list[str] | None
    category: str | None
    project_id: uuid.UUID
    is_shared: bool
    current_version: str
    created_at: datetime
    updated_at: datetime


class RenderRequest(BaseModel):
    variables: dict[str, Any] = {}


class RenderResponse(BaseModel):
    prompt_id: uuid.UUID
    version: str
    rendered_content: str
    variables_used: dict[str, Any]
