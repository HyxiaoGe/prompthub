import hashlib
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import VersionStatus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import PaginationParams
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.scene import Scene
from app.models.version import PromptVersion
from app.schemas.project import ProjectCreate
from app.schemas.prompt import PublishedPromptBundleResponse, PublishedPromptResponse

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "slug"}


async def create_project(
    db: AsyncSession,
    data: ProjectCreate,
    created_by: uuid.UUID | None = None,
) -> Project:
    existing = await db.execute(select(Project).where(Project.slug == data.slug))
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
    db: AsyncSession,
    pagination: PaginationParams,
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
    db: AsyncSession,
    project_id: uuid.UUID,
) -> tuple[Project, int, int]:
    project = await get_project(db, project_id)

    prompt_count_stmt = (
        select(func.count()).select_from(Prompt).where(Prompt.project_id == project_id, Prompt.deleted_at.is_(None))
    )
    prompt_count = (await db.execute(prompt_count_stmt)).scalar_one()

    scene_count_stmt = select(func.count()).select_from(Scene).where(Scene.project_id == project_id)
    scene_count = (await db.execute(scene_count_stmt)).scalar_one()

    return project, prompt_count, scene_count


async def list_project_prompts(
    db: AsyncSession,
    project_id: uuid.UUID,
    pagination: PaginationParams,
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


def _bundle_revision(project_slug: str, prompts: list[PublishedPromptResponse]) -> str:
    canonical = json.dumps(
        {
            "project_slug": project_slug,
            "prompts": [
                {
                    "slug": prompt.slug,
                    "version": prompt.version,
                    "content_sha256": hashlib.sha256(prompt.content.encode("utf-8")).hexdigest(),
                    "variables": prompt.variables,
                }
                for prompt in sorted(prompts, key=lambda item: item.slug)
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def get_published_prompt_bundle(
    db: AsyncSession,
    project_slug: str,
) -> PublishedPromptBundleResponse:
    project = (await db.execute(select(Project).where(Project.slug == project_slug))).scalar_one_or_none()
    if project is None:
        raise NotFoundError(
            message="Project not found",
            detail=f"No project with slug '{project_slug}'",
        )

    current_version_join = (PromptVersion.prompt_id == Prompt.id) & (PromptVersion.version == Prompt.current_version)
    rows = (
        await db.execute(
            select(Prompt, PromptVersion)
            .outerjoin(PromptVersion, current_version_join)
            .where(
                Prompt.project_id == project.id,
                Prompt.deleted_at.is_(None),
            )
            .order_by(Prompt.slug.asc())
        )
    ).all()

    invalid_slugs = [
        prompt.slug for prompt, version in rows if version is None or version.status != VersionStatus.PUBLISHED
    ]
    if invalid_slugs:
        raise ConflictError(
            message="Published prompt bundle is incomplete",
            detail="Current version is missing or not published: " + ", ".join(invalid_slugs),
        )

    prompts = [
        PublishedPromptResponse(
            id=prompt.id,
            slug=prompt.slug,
            name=prompt.name,
            version=version.version,
            status=version.status,
            content=version.content,
            variables=version.variables,
            format=version.format,
            template_engine=version.template_engine,
            published_at=version.created_at,
        )
        for prompt, version in rows
        if version is not None
    ]
    return PublishedPromptBundleResponse(
        project_id=project.id,
        project_slug=project.slug,
        revision=_bundle_revision(project.slug, prompts),
        prompts=prompts,
    )
