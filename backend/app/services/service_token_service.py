import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import SERVICE_TOKEN_PREFIX, hash_service_token
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.project import Project
from app.models.service_token import ServiceToken
from app.models.user import User

READ_SCOPE = "prompts:read"


@dataclass(frozen=True)
class ProvisionResult:
    action: str
    token_id: uuid.UUID | None


def validate_service_token(raw_token: str) -> None:
    if not raw_token.startswith(SERVICE_TOKEN_PREFIX) or len(raw_token) == len(SERVICE_TOKEN_PREFIX):
        raise ValidationError(
            message="Service token prefix is invalid",
            detail=f"Service tokens must use the '{SERVICE_TOKEN_PREFIX}' prefix",
        )


async def _ensure_not_user_api_key(db: AsyncSession, raw_token: str) -> None:
    user = (await db.execute(select(User).where(User.api_key == raw_token))).scalar_one_or_none()
    if user is not None:
        raise ConflictError(
            message="Service token conflicts with a user API key",
            detail="Choose a service token that is not already used by a user",
        )


async def provision_service_token(
    db: AsyncSession,
    *,
    project_slug: str,
    name: str,
    raw_token: str,
    scope: str = READ_SCOPE,
    apply: bool,
) -> ProvisionResult:
    validate_service_token(raw_token)
    if scope != READ_SCOPE:
        raise ValidationError(
            message="Unsupported service token scope",
            detail=f"Only '{READ_SCOPE}' is supported",
        )

    await _ensure_not_user_api_key(db, raw_token)

    project = (await db.execute(select(Project).where(Project.slug == project_slug))).scalar_one_or_none()
    if project is None:
        raise NotFoundError(
            message="Project not found",
            detail=f"No project with slug '{project_slug}'",
        )

    token_hash = hash_service_token(raw_token)
    existing = (
        await db.execute(
            select(ServiceToken).where(
                ServiceToken.project_id == project.id,
                ServiceToken.name == name,
            )
        )
    ).scalar_one_or_none()

    if (
        existing is not None
        and existing.token_hash == token_hash
        and existing.scope == scope
        and existing.revoked_at is None
    ):
        return ProvisionResult(action="unchanged", token_id=existing.id)

    if not apply:
        return ProvisionResult(
            action="would_rotate" if existing is not None else "would_create",
            token_id=existing.id if existing is not None else None,
        )

    if existing is None:
        existing = ServiceToken(
            name=name,
            project_id=project.id,
            token_hash=token_hash,
            scope=scope,
        )
        db.add(existing)
        action = "created"
    else:
        existing.token_hash = token_hash
        existing.scope = scope
        existing.revoked_at = None
        action = "rotated"

    await db.flush()
    return ProvisionResult(action=action, token_id=existing.id)
