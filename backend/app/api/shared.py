import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.pagination import PaginationParams, get_pagination
from app.core.response import pagination_meta, success_response
from app.database import get_db
from app.models.user import User
from app.schemas.prompt import PromptResponse, PromptSummaryResponse
from app.schemas.shared import ForkRequest
from app.services import prompt_service, ref_service

router = APIRouter()


@router.get("/prompts")
async def list_shared_prompts(
    pagination: PaginationParams = Depends(get_pagination),
    search: str | None = Query(None, description="Search name/description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await prompt_service.list_prompts(
        db, pagination, is_shared=True, search=search,
    )
    return success_response(
        data=[PromptSummaryResponse.model_validate(p).model_dump(mode="json") for p in items],
        meta=pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.post("/prompts/{prompt_id}/fork")
async def fork_prompt(
    prompt_id: uuid.UUID,
    data: ForkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    forked = await ref_service.fork_prompt(
        db,
        source_prompt_id=prompt_id,
        target_project_id=data.target_project_id,
        created_by=current_user.id,
        slug_override=data.slug,
    )
    return success_response(data=PromptResponse.model_validate(forked).model_dump(mode="json"))
