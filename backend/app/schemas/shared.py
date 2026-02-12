import uuid

from pydantic import BaseModel


class ForkRequest(BaseModel):
    target_project_id: uuid.UUID
    slug: str | None = None
