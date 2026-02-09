import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.response import success_response
from app.database import get_db
from app.models.user import User
from app.schemas.version import VersionPublishRequest, VersionResponse
from app.services import version_service

router = APIRouter()


@router.get("/{prompt_id}/versions")
async def list_versions(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    versions = await version_service.list_versions(db, prompt_id)
    return success_response(
        data=[VersionResponse.model_validate(v).model_dump(mode="json") for v in versions],
    )


@router.post("/{prompt_id}/publish")
async def publish_version(
    prompt_id: uuid.UUID,
    data: VersionPublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    version = await version_service.publish_version(db, prompt_id, data, created_by=current_user.id)
    return success_response(data=VersionResponse.model_validate(version).model_dump(mode="json"))


@router.get("/{prompt_id}/versions/{version_str}")
async def get_version(
    prompt_id: uuid.UUID,
    version_str: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    version = await version_service.get_version(db, prompt_id, version_str)
    return success_response(data=VersionResponse.model_validate(version).model_dump(mode="json"))
