import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Shared Test Project",
        "slug": f"shared-test-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


@pytest.fixture
async def other_project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Fork Target",
        "slug": f"fork-target-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


async def test_shared_list_only_shared(client: AsyncClient, project_id: str) -> None:
    # Create a shared prompt
    await client.post(f"{API}/prompts", json={
        "name": "Shared One",
        "slug": f"shared-one-{uuid.uuid4().hex[:8]}",
        "content": "shared",
        "project_id": project_id,
        "is_shared": True,
    })
    # Create a private prompt
    await client.post(f"{API}/prompts", json={
        "name": "Private One",
        "slug": f"private-one-{uuid.uuid4().hex[:8]}",
        "content": "private",
        "project_id": project_id,
        "is_shared": False,
    })

    resp = await client.get(f"{API}/shared/prompts")
    body = resp.json()
    assert body["code"] == 0
    # All returned prompts should be shared
    for p in body["data"]:
        assert p["is_shared"] is True


async def test_share_prompt(client: AsyncClient, project_id: str) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Make Shared",
        "slug": f"make-shared-{uuid.uuid4().hex[:8]}",
        "content": "to share",
        "project_id": project_id,
        "is_shared": False,
    })
    prompt_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["is_shared"] is False

    resp = await client.post(f"{API}/prompts/{prompt_id}/share")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_shared"] is True


async def test_fork_shared_prompt(
    client: AsyncClient, project_id: str, other_project_id: str,
) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Original Shared",
        "slug": f"original-shared-{uuid.uuid4().hex[:8]}",
        "content": "forked content",
        "project_id": project_id,
        "is_shared": True,
    })
    source_id = create_resp.json()["data"]["id"]

    resp = await client.post(f"{API}/shared/prompts/{source_id}/fork", json={
        "target_project_id": other_project_id,
    })
    assert resp.status_code == 200
    fork_data = resp.json()["data"]
    assert fork_data["content"] == "forked content"
    assert fork_data["project_id"] == other_project_id
    assert fork_data["is_shared"] is False
    assert "fork" in fork_data["name"].lower()


async def test_fork_non_shared_denied(
    client: AsyncClient, project_id: str, other_project_id: str,
) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Private Prompt",
        "slug": f"private-prompt-{uuid.uuid4().hex[:8]}",
        "content": "private",
        "project_id": project_id,
        "is_shared": False,
    })
    source_id = create_resp.json()["data"]["id"]

    resp = await client.post(f"{API}/shared/prompts/{source_id}/fork", json={
        "target_project_id": other_project_id,
    })
    assert resp.status_code == 403


async def test_render_endpoint(client: AsyncClient, project_id: str) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Render Test",
        "slug": f"render-test-{uuid.uuid4().hex[:8]}",
        "content": "Hello {{ name }}!",
        "project_id": project_id,
        "variables": [{"name": "name", "type": "string", "required": True}],
    })
    prompt_id = create_resp.json()["data"]["id"]

    resp = await client.post(f"{API}/prompts/{prompt_id}/render", json={
        "variables": {"name": "World"},
    })
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["rendered_content"] == "Hello World!"
    assert body["version"] == "1.0.0"
