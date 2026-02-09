import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.prompt import Prompt
from app.models.version import PromptVersion
from app.schemas.version import BumpType, VersionPublishRequest
from app.services.prompt_service import get_prompt


def bump_version(current: str, bump_type: BumpType) -> str:
    parts = current.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == BumpType.MAJOR:
        return f"{major + 1}.0.0"
    elif bump_type == BumpType.MINOR:
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


async def publish_version(
    db: AsyncSession,
    prompt_id: uuid.UUID,
    data: VersionPublishRequest,
    created_by: uuid.UUID | None = None,
) -> PromptVersion:
    prompt = await get_prompt(db, prompt_id)

    new_version_str = bump_version(prompt.current_version, data.bump)

    content = data.content if data.content is not None else prompt.content
    variables = (
        [v if isinstance(v, dict) else v for v in data.variables]
        if data.variables is not None
        else prompt.variables
    )

    version = PromptVersion(
        prompt_id=prompt.id,
        version=new_version_str,
        content=content,
        variables=variables,
        changelog=data.changelog,
        status="published",
        created_by=created_by,
    )
    db.add(version)

    prompt.current_version = new_version_str
    await db.flush()

    return version


async def list_versions(
    db: AsyncSession, prompt_id: uuid.UUID,
) -> list[PromptVersion]:
    # Verify prompt exists
    await get_prompt(db, prompt_id)

    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.created_at.desc())
    )
    return list(result.scalars().all())


async def get_version(
    db: AsyncSession, prompt_id: uuid.UUID, version_str: str,
) -> PromptVersion:
    # Verify prompt exists
    await get_prompt(db, prompt_id)

    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version_str,
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise NotFoundError(
            message="Version not found",
            detail=f"No version '{version_str}' for prompt '{prompt_id}'",
        )
    return version
