import hashlib
import uuid
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, PermissionError
from app.database import get_db
from app.models.project import Project
from app.models.service_token import ServiceToken
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
SERVICE_TOKEN_PREFIX = "phs_"


@dataclass(frozen=True)
class BundlePrincipal:
    user_id: uuid.UUID | None = None
    service_token_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


def hash_service_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationError(detail="Authorization header missing")

    api_key = credentials.credentials
    if api_key.startswith(SERVICE_TOKEN_PREFIX):
        raise AuthenticationError(detail="Service tokens are not allowed for user APIs")

    result = await db.execute(select(User).where(User.api_key == api_key))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError(detail="Invalid API key")

    return user


async def get_bundle_principal(
    project_slug: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> BundlePrincipal:
    if credentials is None:
        raise AuthenticationError(detail="Authorization header missing")

    raw_token = credentials.credentials
    if raw_token.startswith(SERVICE_TOKEN_PREFIX):
        token_hash = hash_service_token(raw_token)
        service_token = (
            await db.execute(
                select(ServiceToken).where(
                    ServiceToken.token_hash == token_hash,
                    ServiceToken.scope == "prompts:read",
                    ServiceToken.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if service_token is None:
            raise AuthenticationError(detail="Invalid API key")

        project = (await db.execute(select(Project).where(Project.slug == project_slug))).scalar_one_or_none()
        if project is not None and service_token.project_id != project.id:
            raise PermissionError(detail="Service token is bound to another project")

        return BundlePrincipal(
            service_token_id=service_token.id,
            project_id=service_token.project_id,
        )

    user = (await db.execute(select(User).where(User.api_key == raw_token))).scalar_one_or_none()
    if user is None:
        raise AuthenticationError(detail="Invalid API key")
    return BundlePrincipal(user_id=user.id)
