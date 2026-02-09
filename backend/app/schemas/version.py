import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class BumpType(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


class VersionPublishRequest(BaseModel):
    changelog: str | None = None
    bump: BumpType = BumpType.PATCH
    content: str | None = None
    variables: list[Any] | None = None


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    version: str
    content: str
    variables: Any
    changelog: str | None
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
