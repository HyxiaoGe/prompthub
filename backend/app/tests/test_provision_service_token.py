import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.database import async_engine
from app.models.service_token import ServiceToken
from app.models.user import User
from app.services.service_token_service import (
    _ensure_not_user_api_key,
    provision_service_token,
    validate_service_token,
)
from scripts.provision_service_token import load_config


def test_provision_config_requires_secret_without_exposing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPTHUB_SERVICE_TOKEN_PROJECT_SLUG", "fusion")
    monkeypatch.setenv("PROMPTHUB_SERVICE_TOKEN_NAME", "fusion-runtime")
    monkeypatch.delenv("PROMPTHUB_SERVICE_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="PROMPTHUB_SERVICE_TOKEN"):
        load_config()


def test_provision_config_reads_hash_input_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPTHUB_SERVICE_TOKEN_PROJECT_SLUG", "fusion")
    monkeypatch.setenv("PROMPTHUB_SERVICE_TOKEN_NAME", "fusion-runtime")
    monkeypatch.setenv("PROMPTHUB_SERVICE_TOKEN", "phs_secret")

    config = load_config()

    assert config.project_slug == "fusion"
    assert config.name == "fusion-runtime"
    assert config.raw_token == "phs_secret"
    assert "phs_secret" not in repr(config)


def test_service_token_requires_dedicated_prefix() -> None:
    with pytest.raises(ValidationError, match="prefix"):
        validate_service_token("shared-user-key")

    validate_service_token("phs_valid-service-token")


async def test_service_token_rejects_existing_user_api_key() -> None:
    db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = object()
    db.execute.return_value = result

    with pytest.raises(ConflictError, match="user API key"):
        await _ensure_not_user_api_key(db, "phs_conflicting-key")


def test_database_engine_hides_bound_parameters() -> None:
    assert async_engine.sync_engine.hide_parameters is True


async def test_provision_service_token_is_dry_run_idempotent_and_hash_only(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    project_slug = f"token-project-{uuid.uuid4().hex[:8]}"
    project = (
        await client.post(
            "/api/v1/projects",
            json={"name": "Token Project", "slug": project_slug},
        )
    ).json()["data"]
    raw_token = "phs_first-secret"

    dry_run = await provision_service_token(
        db_session,
        project_slug=project_slug,
        name="fusion-runtime",
        raw_token=raw_token,
        apply=False,
    )
    token_query = select(ServiceToken).where(
        ServiceToken.project_id == uuid.UUID(project["id"]),
        ServiceToken.name == "fusion-runtime",
    )
    token_before_apply = (await db_session.execute(token_query)).scalar_one_or_none()
    assert dry_run.action == "would_create"
    assert token_before_apply is None

    created = await provision_service_token(
        db_session,
        project_slug=project_slug,
        name="fusion-runtime",
        raw_token=raw_token,
        apply=True,
    )
    unchanged = await provision_service_token(
        db_session,
        project_slug=project_slug,
        name="fusion-runtime",
        raw_token=raw_token,
        apply=True,
    )
    rotated = await provision_service_token(
        db_session,
        project_slug=project_slug,
        name="fusion-runtime",
        raw_token="phs_rotated-secret",
        apply=True,
    )

    token = (await db_session.execute(token_query)).scalar_one()
    assert created.action == "created"
    assert unchanged.action == "unchanged"
    assert rotated.action == "rotated"
    assert created.token_id == unchanged.token_id == rotated.token_id
    assert token.token_hash == hashlib.sha256(b"phs_rotated-secret").hexdigest()
    assert raw_token not in token.token_hash


@pytest.mark.parametrize("apply", [False, True])
async def test_provision_rejects_user_key_for_create(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    apply: bool,
) -> None:
    project_slug = f"collision-project-{uuid.uuid4().hex[:8]}"
    await client.post(
        "/api/v1/projects",
        json={"name": "Collision Project", "slug": project_slug},
    )
    test_user.api_key = "phs_existing-user-key"
    await db_session.flush()

    with pytest.raises(ConflictError, match="user API key"):
        await provision_service_token(
            db_session,
            project_slug=project_slug,
            name="fusion-runtime",
            raw_token=test_user.api_key,
            apply=apply,
        )


async def test_provision_rejects_user_key_for_rotation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    project_slug = f"rotation-project-{uuid.uuid4().hex[:8]}"
    await client.post(
        "/api/v1/projects",
        json={"name": "Rotation Project", "slug": project_slug},
    )
    created = await provision_service_token(
        db_session,
        project_slug=project_slug,
        name="fusion-runtime",
        raw_token="phs_original-service-token",
        apply=True,
    )
    conflicting_key = "phs_existing-user-key-for-rotation"
    db_session.add(
        User(
            id=uuid.uuid4(),
            email=f"rotation-{uuid.uuid4().hex[:8]}@test.dev",
            name="Rotation Collision User",
            role="admin",
            api_key=conflicting_key,
        )
    )
    await db_session.flush()

    with pytest.raises(ConflictError, match="user API key"):
        await provision_service_token(
            db_session,
            project_slug=project_slug,
            name="fusion-runtime",
            raw_token=conflicting_key,
            apply=True,
        )

    token = (await db_session.execute(select(ServiceToken).where(ServiceToken.id == created.token_id))).scalar_one()
    assert token.token_hash == hashlib.sha256(b"phs_original-service-token").hexdigest()
