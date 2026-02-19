import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.enums import BumpType, VersionStatus


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
    status: VersionStatus
    created_by: uuid.UUID | None
    created_at: datetime
