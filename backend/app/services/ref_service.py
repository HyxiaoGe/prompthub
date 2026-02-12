import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionError
from app.models.prompt import Prompt
from app.models.prompt_ref import PromptRef
from app.models.scene import Scene
from app.services.dependency_resolver import check_no_cycles
from app.services.prompt_service import get_prompt


async def create_ref(
    db: AsyncSession,
    source_prompt_id: uuid.UUID,
    target_prompt_id: uuid.UUID,
    ref_type: str,
    override_config: dict | None = None,
) -> PromptRef:
    """Create a prompt reference with cycle detection."""
    source = await get_prompt(db, source_prompt_id)
    target = await get_prompt(db, target_prompt_id)

    # Cross-project: target must be shared
    if source.project_id != target.project_id and not target.is_shared:
        raise PermissionError(
            message="Cross-project reference denied",
            detail=f"Target prompt '{target.name}' is not shared",
        )

    # Cycle detection
    await check_no_cycles(db, source_prompt_id, target_prompt_id)

    ref = PromptRef(
        source_prompt_id=source_prompt_id,
        target_prompt_id=target_prompt_id,
        source_project_id=source.project_id,
        target_project_id=target.project_id,
        ref_type=ref_type,
        override_config=override_config or {},
    )
    db.add(ref)
    await db.flush()
    return ref


async def delete_ref(db: AsyncSession, ref_id: uuid.UUID) -> None:
    result = await db.execute(select(PromptRef).where(PromptRef.id == ref_id))
    ref = result.scalar_one_or_none()
    if ref is None:
        raise NotFoundError(message="Reference not found", detail=f"No ref with id '{ref_id}'")
    await db.delete(ref)
    await db.flush()


async def list_refs_for_prompt(
    db: AsyncSession, prompt_id: uuid.UUID,
) -> tuple[list[PromptRef], list[PromptRef]]:
    """Return (outgoing_refs, incoming_refs) for a prompt."""
    await get_prompt(db, prompt_id)  # ensure exists

    outgoing_result = await db.execute(
        select(PromptRef).where(PromptRef.source_prompt_id == prompt_id)
    )
    outgoing = list(outgoing_result.scalars().all())

    incoming_result = await db.execute(
        select(PromptRef).where(PromptRef.target_prompt_id == prompt_id)
    )
    incoming = list(incoming_result.scalars().all())

    return outgoing, incoming


async def get_impact_analysis(
    db: AsyncSession, prompt_id: uuid.UUID,
) -> list[Scene]:
    """Find all scenes whose pipeline references this prompt."""
    await get_prompt(db, prompt_id)

    # Query scenes where pipeline JSONB contains this prompt_id
    # Use JSONB cast + text matching since pipeline is nested
    result = await db.execute(
        select(Scene).where(
            Scene.pipeline.cast(str).contains(str(prompt_id))
        )
    )
    return list(result.scalars().all())


async def fork_prompt(
    db: AsyncSession,
    source_prompt_id: uuid.UUID,
    target_project_id: uuid.UUID,
    created_by: uuid.UUID | None = None,
    slug_override: str | None = None,
) -> Prompt:
    """Fork a shared prompt into a target project."""
    source = await get_prompt(db, source_prompt_id)

    if not source.is_shared:
        raise PermissionError(
            message="Cannot fork non-shared prompt",
            detail=f"Prompt '{source.name}' is not shared",
        )

    new_slug = slug_override or f"{source.slug}-fork"

    forked = Prompt(
        name=f"{source.name} (fork)",
        slug=new_slug,
        description=source.description,
        content=source.content,
        format=source.format,
        template_engine=source.template_engine,
        variables=source.variables,
        tags=source.tags,
        category=source.category,
        project_id=target_project_id,
        is_shared=False,
        current_version="1.0.0",
        created_by=created_by,
    )
    db.add(forked)
    await db.flush()

    # Create ref linking fork to original
    ref = PromptRef(
        source_prompt_id=forked.id,
        target_prompt_id=source.id,
        source_project_id=target_project_id,
        target_project_id=source.project_id,
        ref_type="includes",
    )
    db.add(ref)
    await db.flush()

    return forked
