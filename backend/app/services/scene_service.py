import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PermissionError, ValidationError
from app.core.pagination import PaginationParams
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.scene import Scene
from app.schemas.scene import PipelineConfig, SceneCreate, SceneUpdate
from app.services.dependency_resolver import build_full_ref_graph, topological_sort_with_cycle_detection

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "slug"}


async def _validate_pipeline_prompts(
    db: AsyncSession,
    pipeline: PipelineConfig,
    project_id: uuid.UUID,
) -> None:
    """Validate all prompt_ids in pipeline exist and are accessible."""
    prompt_ids = {step.prompt_ref.prompt_id for step in pipeline.steps}
    if not prompt_ids:
        return

    result = await db.execute(
        select(Prompt).where(Prompt.id.in_(prompt_ids), Prompt.deleted_at.is_(None))
    )
    found_prompts = {p.id: p for p in result.scalars().all()}

    missing = prompt_ids - set(found_prompts.keys())
    if missing:
        raise NotFoundError(
            message="Prompt not found",
            detail=f"Prompts not found: {[str(m) for m in missing]}",
        )

    # Cross-project check: must be shared
    for pid, prompt in found_prompts.items():
        if prompt.project_id != project_id and not prompt.is_shared:
            raise PermissionError(
                message="Cross-project reference denied",
                detail=f"Prompt '{prompt.name}' ({pid}) is not shared and belongs to another project",
            )


async def _check_pipeline_cycles(
    db: AsyncSession,
    pipeline: PipelineConfig,
) -> None:
    """Check for circular dependencies in the pipeline."""
    prompt_ids = {step.prompt_ref.prompt_id for step in pipeline.steps}
    if not prompt_ids:
        return
    graph = await build_full_ref_graph(db, prompt_ids)
    topological_sort_with_cycle_detection(graph)


async def create_scene(
    db: AsyncSession,
    data: SceneCreate,
    created_by: uuid.UUID | None = None,
) -> Scene:
    # Verify project exists
    project = await db.execute(select(Project).where(Project.id == data.project_id))
    if project.scalar_one_or_none() is None:
        raise NotFoundError(
            message="Project not found",
            detail=f"No project with id '{data.project_id}'",
        )

    # Check slug uniqueness within project
    existing = await db.execute(
        select(Scene).where(
            Scene.project_id == data.project_id,
            Scene.slug == data.slug,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            message="Scene slug already exists",
            detail=f"A scene with slug '{data.slug}' already exists in this project",
        )

    # Validate pipeline prompts
    await _validate_pipeline_prompts(db, data.pipeline, data.project_id)

    # Check for cycles
    await _check_pipeline_cycles(db, data.pipeline)

    scene = Scene(
        name=data.name,
        slug=data.slug,
        description=data.description,
        project_id=data.project_id,
        pipeline=data.pipeline.model_dump(mode="json"),
        merge_strategy=data.merge_strategy,
        separator=data.separator,
        output_format=data.output_format,
        created_by=created_by,
    )
    db.add(scene)
    await db.flush()
    return scene


async def get_scene(db: AsyncSession, scene_id: uuid.UUID) -> Scene:
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if scene is None:
        raise NotFoundError(
            message="Scene not found",
            detail=f"No scene with id '{scene_id}'",
        )
    return scene


async def list_scenes(
    db: AsyncSession,
    pagination: PaginationParams,
    *,
    project_id: uuid.UUID | None = None,
) -> tuple[list[Scene], int]:
    if pagination.sort_by not in ALLOWED_SORT_FIELDS:
        raise ValidationError(
            message="Invalid sort field",
            detail=f"sort_by must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    base = select(Scene)
    if project_id is not None:
        base = base.where(Scene.project_id == project_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    order_col = getattr(Scene, pagination.sort_by)
    stmt = base.order_by(order_col.asc() if pagination.order == "asc" else order_col.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def update_scene(
    db: AsyncSession,
    scene_id: uuid.UUID,
    data: SceneUpdate,
) -> Scene:
    scene = await get_scene(db, scene_id)
    update_data = data.model_dump(exclude_unset=True)

    if "pipeline" in update_data and data.pipeline is not None:
        await _validate_pipeline_prompts(db, data.pipeline, scene.project_id)
        await _check_pipeline_cycles(db, data.pipeline)
        update_data["pipeline"] = data.pipeline.model_dump(mode="json")

    for field, value in update_data.items():
        setattr(scene, field, value)

    await db.flush()
    await db.refresh(scene)
    return scene


async def delete_scene(db: AsyncSession, scene_id: uuid.UUID) -> None:
    scene = await get_scene(db, scene_id)
    await db.delete(scene)
    await db.flush()
