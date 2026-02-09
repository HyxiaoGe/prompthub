import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import PaginationParams
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.scene import Scene
from app.schemas.project import ProjectCreate, ProjectUpdate

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "slug"}


async def create_project(
    db: AsyncSession, data: ProjectCreate, created_by: uuid.UUID | None = None,
) -> Project:
    existing = await db.execute(
        select(Project).where(Project.slug == data.slug)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            message="Project slug already exists",
            detail=f"A project with slug '{data.slug}' already exists",
        )

    project = Project(
        name=data.name,
        slug=data.slug,
        description=data.description,
        created_by=created_by,
    )
    db.add(project)
    await db.flush()
    return project


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError(
            message="Project not found",
            detail=f"No project with id '{project_id}'",
        )
    return project


async def list_projects(
    db: AsyncSession, pagination: PaginationParams,
) -> tuple[list[Project], int]:
    if pagination.sort_by not in ALLOWED_SORT_FIELDS:
        raise ValidationError(
            message="Invalid sort field",
            detail=f"sort_by must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    # Count
    count_stmt = select(func.count()).select_from(Project)
    total = (await db.execute(count_stmt)).scalar_one()

    # Query
    stmt = select(Project)
    order_col = getattr(Project, pagination.sort_by)
    stmt = stmt.order_by(order_col.asc() if pagination.order == "asc" else order_col.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def get_project_with_counts(
    db: AsyncSession, project_id: uuid.UUID,
) -> tuple[Project, int, int]:
    project = await get_project(db, project_id)

    prompt_count_stmt = (
        select(func.count())
        .select_from(Prompt)
        .where(Prompt.project_id == project_id, Prompt.deleted_at.is_(None))
    )
    prompt_count = (await db.execute(prompt_count_stmt)).scalar_one()

    scene_count_stmt = (
        select(func.count())
        .select_from(Scene)
        .where(Scene.project_id == project_id)
    )
    scene_count = (await db.execute(scene_count_stmt)).scalar_one()

    return project, prompt_count, scene_count


async def list_project_prompts(
    db: AsyncSession, project_id: uuid.UUID, pagination: PaginationParams,
) -> tuple[list[Prompt], int]:
    # Verify project exists
    await get_project(db, project_id)

    base = select(Prompt).where(
        Prompt.project_id == project_id,
        Prompt.deleted_at.is_(None),
    )

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Sort
    allowed = {"created_at", "updated_at", "name", "slug"}
    sort_field = pagination.sort_by if pagination.sort_by in allowed else "created_at"
    order_col = getattr(Prompt, sort_field)
    stmt = base.order_by(order_col.asc() if pagination.order == "asc" else order_col.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total
