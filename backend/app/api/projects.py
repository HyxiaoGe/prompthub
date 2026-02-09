import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.pagination import PaginationParams, get_pagination
from app.core.response import pagination_meta, success_response
from app.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.prompt import PromptSummaryResponse
from app.services import project_service

router = APIRouter()


@router.post("")
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    project = await project_service.create_project(db, data, created_by=current_user.id)
    return success_response(data=ProjectResponse.model_validate(project).model_dump(mode="json"))


@router.get("")
async def list_projects(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await project_service.list_projects(db, pagination)
    return success_response(
        data=[ProjectResponse.model_validate(p).model_dump(mode="json") for p in items],
        meta=pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    project, prompt_count, scene_count = await project_service.get_project_with_counts(
        db, project_id
    )
    detail = ProjectDetailResponse.model_validate(project)
    detail.prompt_count = prompt_count
    detail.scene_count = scene_count
    return success_response(data=detail.model_dump(mode="json"))


@router.get("/{project_id}/prompts")
async def list_project_prompts(
    project_id: uuid.UUID,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await project_service.list_project_prompts(db, project_id, pagination)
    return success_response(
        data=[PromptSummaryResponse.model_validate(p).model_dump(mode="json") for p in items],
        meta=pagination_meta(pagination.page, pagination.page_size, total),
    )
