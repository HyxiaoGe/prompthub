import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.pagination import PaginationParams, get_pagination
from app.core.response import pagination_meta, success_response
from app.database import get_db
from app.models.user import User
from app.schemas.prompt import (
    PromptCreate,
    PromptResponse,
    PromptSummaryResponse,
    PromptUpdate,
    RenderRequest,
    RenderResponse,
)
from app.services import prompt_service, template_engine

router = APIRouter()


@router.post("")
async def create_prompt(
    data: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prompt = await prompt_service.create_prompt(db, data, created_by=current_user.id)
    return success_response(data=PromptResponse.model_validate(prompt).model_dump(mode="json"))


@router.get("")
async def list_prompts(
    pagination: PaginationParams = Depends(get_pagination),
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    slug: str | None = Query(None, description="Filter by exact slug"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    category: str | None = Query(None, description="Filter by category"),
    is_shared: bool | None = Query(None, description="Filter shared prompts"),
    search: str | None = Query(None, description="Search name/description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    items, total = await prompt_service.list_prompts(
        db,
        pagination,
        project_id=project_id,
        slug=slug,
        tags=tags_list,
        category=category,
        is_shared=is_shared,
        search=search,
    )
    return success_response(
        data=[PromptSummaryResponse.model_validate(p).model_dump(mode="json") for p in items],
        meta=pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prompt = await prompt_service.get_prompt(db, prompt_id)
    return success_response(data=PromptResponse.model_validate(prompt).model_dump(mode="json"))


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: uuid.UUID,
    data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prompt = await prompt_service.update_prompt(db, prompt_id, data)
    return success_response(data=PromptResponse.model_validate(prompt).model_dump(mode="json"))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await prompt_service.delete_prompt(db, prompt_id)
    return success_response()


@router.post("/{prompt_id}/render")
async def render_prompt(
    prompt_id: uuid.UUID,
    data: RenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prompt = await prompt_service.get_prompt(db, prompt_id)
    var_defs = prompt.variables or []
    rendered = template_engine.render_prompt(prompt.content, var_defs, data.variables)
    response = RenderResponse(
        prompt_id=prompt.id,
        version=prompt.current_version,
        rendered_content=rendered,
        variables_used=data.variables,
    )
    return success_response(data=response.model_dump(mode="json"))


@router.post("/{prompt_id}/share")
async def share_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prompt = await prompt_service.get_prompt(db, prompt_id)
    prompt.is_shared = True
    await db.flush()
    await db.refresh(prompt)
    return success_response(data=PromptResponse.model_validate(prompt).model_dump(mode="json"))
