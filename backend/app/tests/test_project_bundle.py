import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.service_token import ServiceToken
from app.models.user import User
from app.models.version import PromptVersion
from app.schemas.prompt import PublishedPromptResponse
from app.services.project_service import _bundle_revision

API = "/api/v1"


def _published_prompt() -> PublishedPromptResponse:
    return PublishedPromptResponse(
        id=uuid.uuid4(),
        slug="runtime",
        name="Runtime Prompt",
        version="1.0.0",
        status="published",
        content="content",
        variables=[],
        format="text",
        template_engine="jinja2",
        published_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", uuid.uuid4()),
        ("name", "Runtime Prompt v2"),
        ("status", "deprecated"),
        ("format", "chat"),
        ("template_engine", "none"),
    ],
)
def test_bundle_revision_ignores_delivery_metadata(field: str, value: object) -> None:
    base = _published_prompt()
    changed = base.model_copy(update={field: value})

    assert _bundle_revision("fusion", [base]) == _bundle_revision("fusion", [changed])


def test_bundle_revision_excludes_published_at() -> None:
    base = _published_prompt()
    rebuilt = base.model_copy(update={"published_at": base.published_at + timedelta(days=1)})

    assert _bundle_revision("fusion", [base]) == _bundle_revision("fusion", [rebuilt])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("slug", "runtime-v2"),
        ("version", "1.0.1"),
        ("content", "changed"),
        ("variables", [{"name": "topic"}]),
    ],
)
def test_bundle_revision_covers_runtime_contract(field: str, value: object) -> None:
    base = _published_prompt()
    changed = base.model_copy(update={field: value})

    assert _bundle_revision("fusion", [base]) != _bundle_revision("fusion", [changed])


def test_bundle_revision_covers_project_slug() -> None:
    prompt = _published_prompt()

    assert _bundle_revision("fusion", [prompt]) != _bundle_revision("other", [prompt])


def test_bundle_revision_uses_sorted_content_hash_contract() -> None:
    first = _published_prompt().model_copy(update={"slug": "z-last"})
    second = _published_prompt().model_copy(update={"slug": "a-first", "content": "second"})
    canonical = json.dumps(
        {
            "project_slug": "fusion",
            "prompts": [
                {
                    "slug": "a-first",
                    "version": "1.0.0",
                    "content_sha256": hashlib.sha256(b"second").hexdigest(),
                    "variables": [],
                },
                {
                    "slug": "z-last",
                    "version": "1.0.0",
                    "content_sha256": hashlib.sha256(b"content").hexdigest(),
                    "variables": [],
                },
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    assert _bundle_revision("fusion", [first, second]) == expected
    assert _bundle_revision("fusion", [second, first]) == expected


@pytest.fixture
async def bundle_project(client: AsyncClient) -> tuple[str, str, dict[str, str]]:
    slug = f"bundle-{uuid.uuid4().hex[:8]}"
    project = (
        await client.post(
            f"{API}/projects",
            json={"name": "Bundle Project", "slug": slug},
        )
    ).json()["data"]

    ids: dict[str, str] = {}
    for prompt_slug, content in (("z-last", "z v1"), ("a-first", "a v1")):
        prompt = (
            await client.post(
                f"{API}/prompts",
                json={
                    "name": prompt_slug,
                    "slug": prompt_slug,
                    "content": content,
                    "variables": [{"name": "name", "type": "string"}],
                    "project_id": project["id"],
                },
            )
        ).json()["data"]
        ids[prompt_slug] = prompt["id"]

    return slug, project["id"], ids


async def test_published_bundle_uses_current_published_versions_and_stable_revision(
    client: AsyncClient,
    bundle_project: tuple[str, str, dict[str, str]],
) -> None:
    project_slug, _, ids = bundle_project
    await client.put(
        f"{API}/prompts/{ids['a-first']}",
        json={"content": "unpublished edit", "format": "chat"},
    )

    first = await client.get(f"{API}/projects/by-slug/{project_slug}/prompts/published")
    second = await client.get(f"{API}/projects/by-slug/{project_slug}/prompts/published")

    assert first.status_code == 200
    assert first.json()["data"] == second.json()["data"]
    data = first.json()["data"]
    assert data["project_id"]
    assert data["project_slug"] == project_slug
    assert len(data["revision"]) == 64
    int(data["revision"], 16)
    assert [item["slug"] for item in data["prompts"]] == ["a-first", "z-last"]
    assert data["prompts"][0]["content"] == "a v1"
    assert data["prompts"][0]["version"] == "1.0.0"
    assert data["prompts"][0]["status"] == "published"
    assert data["prompts"][0]["name"] == "a-first"
    assert data["prompts"][0]["format"] == "text"
    assert data["prompts"][0]["template_engine"] == "jinja2"
    assert data["prompts"][0]["published_at"]


async def test_published_bundle_fails_when_current_version_is_not_published(
    client: AsyncClient,
    db_session: AsyncSession,
    bundle_project: tuple[str, str, dict[str, str]],
) -> None:
    project_slug, _, ids = bundle_project
    version = (
        await db_session.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == uuid.UUID(ids["a-first"]),
                PromptVersion.version == "1.0.0",
            )
        )
    ).scalar_one()
    version.status = "draft"
    await db_session.flush()

    response = await client.get(f"{API}/projects/by-slug/{project_slug}/prompts/published")

    assert response.status_code == 409
    assert "a-first" in response.json()["detail"]


async def test_published_bundle_fails_when_current_version_is_missing(
    client: AsyncClient,
    db_session: AsyncSession,
    bundle_project: tuple[str, str, dict[str, str]],
) -> None:
    project_slug, _, ids = bundle_project
    await db_session.execute(delete(PromptVersion).where(PromptVersion.prompt_id == uuid.UUID(ids["z-last"])))
    await db_session.flush()

    response = await client.get(f"{API}/projects/by-slug/{project_slug}/prompts/published")

    assert response.status_code == 409
    assert "z-last" in response.json()["detail"]


async def test_project_service_token_only_reads_its_own_bundle(
    unauthed_client: AsyncClient,
    db_session: AsyncSession,
    bundle_project: tuple[str, str, dict[str, str]],
) -> None:
    project_slug, project_id, _ = bundle_project
    other_slug = f"other-{uuid.uuid4().hex[:8]}"
    other_project = Project(id=uuid.uuid4(), name="Other Project", slug=other_slug)
    db_session.add(other_project)
    raw_token = f"phs_{uuid.uuid4().hex}"
    service_token = ServiceToken(
        id=uuid.uuid4(),
        name="fusion-runtime",
        project_id=uuid.UUID(project_id),
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        scope="prompts:read",
    )
    db_session.add(service_token)
    db_session.add(
        User(
            id=uuid.uuid4(),
            email=f"collision-{uuid.uuid4().hex[:8]}@test.dev",
            name="Collision User",
            role="admin",
            api_key=raw_token,
        )
    )
    await db_session.flush()
    headers = {"Authorization": f"Bearer {raw_token}"}

    own = await unauthed_client.get(
        f"{API}/projects/by-slug/{project_slug}/prompts/published",
        headers=headers,
    )
    other = await unauthed_client.get(
        f"{API}/projects/by-slug/{other_slug}/prompts/published",
        headers=headers,
    )
    user_api = await unauthed_client.get(f"{API}/projects", headers=headers)

    assert own.status_code == 200
    assert other.status_code == 403
    assert user_api.status_code == 401


async def test_service_token_requires_prompts_read_scope(
    unauthed_client: AsyncClient,
    db_session: AsyncSession,
    bundle_project: tuple[str, str, dict[str, str]],
) -> None:
    project_slug, project_id, _ = bundle_project
    raw_token = f"phs_{uuid.uuid4().hex}"
    db_session.add(
        ServiceToken(
            id=uuid.uuid4(),
            name="wrong-scope",
            project_id=uuid.UUID(project_id),
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            scope="prompts:write",
        )
    )
    await db_session.flush()

    response = await unauthed_client.get(
        f"{API}/projects/by-slug/{project_slug}/prompts/published",
        headers={"Authorization": f"Bearer {raw_token}"},
    )

    assert response.status_code == 401
