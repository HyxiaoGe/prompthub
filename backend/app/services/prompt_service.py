import uuid

from sqlalchemy import ARRAY, String, cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import PaginationParams
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.version import PromptVersion
from app.schemas.prompt import PromptCreate, PromptUpdate

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "slug", "current_version"}


async def create_prompt(
    db: AsyncSession, data: PromptCreate, created_by: uuid.UUID | None = None,
) -> Prompt:
    # Verify project exists
    project = await db.execute(select(Project).where(Project.id == data.project_id))
    if project.scalar_one_or_none() is None:
        raise NotFoundError(
            message="Project not found",
            detail=f"No project with id '{data.project_id}'",
        )

    # Check slug uniqueness within project
    existing = await db.execute(
        select(Prompt).where(
            Prompt.project_id == data.project_id,
            Prompt.slug == data.slug,
            Prompt.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            message="Prompt slug already exists",
            detail=f"A prompt with slug '{data.slug}' already exists in this project",
        )

    # Serialize variables
    variables_data = [v.model_dump() for v in data.variables] if data.variables else []

    prompt = Prompt(
        name=data.name,
        slug=data.slug,
        description=data.description,
        content=data.content,
        format=data.format,
        template_engine=data.template_engine,
        variables=variables_data,
        tags=data.tags,
        category=data.category,
        project_id=data.project_id,
        is_shared=data.is_shared,
        current_version="1.0.0",
        created_by=created_by,
    )
    db.add(prompt)
    await db.flush()

    # Create initial version
    initial_version = PromptVersion(
        prompt_id=prompt.id,
        version="1.0.0",
        content=data.content,
        variables=variables_data,
        changelog="Initial version",
        status="published",
        created_by=created_by,
    )
    db.add(initial_version)
    await db.flush()

    return prompt


async def get_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> Prompt:
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.deleted_at.is_(None))
    )
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise NotFoundError(
            message="Prompt not found",
            detail=f"No prompt with id '{prompt_id}'",
        )
    return prompt


async def list_prompts(
    db: AsyncSession,
    pagination: PaginationParams,
    *,
    project_id: uuid.UUID | None = None,
    slug: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
    is_shared: bool | None = None,
    search: str | None = None,
) -> tuple[list[Prompt], int]:
    if pagination.sort_by not in ALLOWED_SORT_FIELDS:
        raise ValidationError(
            message="Invalid sort field",
            detail=f"sort_by must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    base = select(Prompt).where(Prompt.deleted_at.is_(None))

    if project_id is not None:
        base = base.where(Prompt.project_id == project_id)
    if slug is not None:
        base = base.where(Prompt.slug == slug)
    if tags:
        # PostgreSQL array overlap operator (&&)
        base = base.where(Prompt.tags.op("&&")(cast(tags, ARRAY(String))))
    if category is not None:
        base = base.where(Prompt.category == category)
    if is_shared is not None:
        base = base.where(Prompt.is_shared == is_shared)
    if search:
        search_pattern = f"%{search}%"
        base = base.where(
            Prompt.name.ilike(search_pattern) | Prompt.description.ilike(search_pattern)
        )

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Sort
    order_col = getattr(Prompt, pagination.sort_by)
    stmt = base.order_by(order_col.asc() if pagination.order == "asc" else order_col.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def update_prompt(
    db: AsyncSession, prompt_id: uuid.UUID, data: PromptUpdate,
) -> Prompt:
    prompt = await get_prompt(db, prompt_id)

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(prompt, field, value)

    try:
        await db.flush()
    except IntegrityError:
        raise ConflictError(
            message="Prompt slug conflict",
            detail="Another prompt with this slug already exists in the project",
        )

    await db.refresh(prompt)
    return prompt


async def delete_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> None:
    prompt = await get_prompt(db, prompt_id)
    prompt.deleted_at = func.now()  # type: ignore[assignment]
    await db.flush()
