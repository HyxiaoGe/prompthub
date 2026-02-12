import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.pagination import PaginationParams, get_pagination
from app.core.response import pagination_meta, success_response
from app.database import get_db
from app.models.user import User
from app.schemas.scene import SceneCreate, SceneResolveRequest, SceneResponse, SceneUpdate
from app.services import scene_engine, scene_service
from app.services.dependency_resolver import get_scene_dependency_graph

router = APIRouter()


@router.post("")
async def create_scene(
    data: SceneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    scene = await scene_service.create_scene(db, data, created_by=current_user.id)
    return success_response(data=SceneResponse.model_validate(scene).model_dump(mode="json"))


@router.get("")
async def list_scenes(
    pagination: PaginationParams = Depends(get_pagination),
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await scene_service.list_scenes(db, pagination, project_id=project_id)
    return success_response(
        data=[SceneResponse.model_validate(s).model_dump(mode="json") for s in items],
        meta=pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/{scene_id}")
async def get_scene(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    scene = await scene_service.get_scene(db, scene_id)
    return success_response(data=SceneResponse.model_validate(scene).model_dump(mode="json"))


@router.put("/{scene_id}")
async def update_scene(
    scene_id: uuid.UUID,
    data: SceneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    scene = await scene_service.update_scene(db, scene_id, data)
    return success_response(data=SceneResponse.model_validate(scene).model_dump(mode="json"))


@router.delete("/{scene_id}")
async def delete_scene(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await scene_service.delete_scene(db, scene_id)
    return success_response()


@router.post("/{scene_id}/resolve")
async def resolve_scene(
    scene_id: uuid.UUID,
    data: SceneResolveRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    caller_ip = request.client.host if request.client else None
    result = await scene_engine.resolve_scene(db, scene_id, data, caller_ip=caller_ip)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{scene_id}/dependencies")
async def get_dependencies(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    graph = await get_scene_dependency_graph(db, scene_id)
    return success_response(data=graph.model_dump(mode="json"))
