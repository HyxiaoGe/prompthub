import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.fixture
async def prompt_id(client: AsyncClient) -> str:
    proj_resp = await client.post(f"{API}/projects", json={
        "name": "Version Test Project",
        "slug": f"ver-test-{uuid.uuid4().hex[:8]}",
    })
    project_id = proj_resp.json()["data"]["id"]

    prompt_resp = await client.post(f"{API}/prompts", json={
        "name": "Version Prompt",
        "slug": f"ver-prompt-{uuid.uuid4().hex[:8]}",
        "content": "original content",
        "project_id": project_id,
    })
    return prompt_resp.json()["data"]["id"]


async def test_publish_patch_version(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "patch",
        "changelog": "patch fix",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["version"] == "1.0.1"
    assert data["created_by"] is not None


async def test_publish_minor_version(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "minor",
        "changelog": "minor update",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] == "1.1.0"


async def test_publish_major_version(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "major",
        "changelog": "breaking change",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] == "2.0.0"


async def test_publish_with_content_override(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "patch",
        "content": "overridden content",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["content"] == "overridden content"


async def test_publish_nonexistent_prompt(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/prompts/{uuid.uuid4()}/publish", json={
        "bump": "patch",
    })
    assert resp.status_code == 404


async def test_publish_no_auth(unauthed_client: AsyncClient) -> None:
    resp = await unauthed_client.post(f"{API}/prompts/{uuid.uuid4()}/publish", json={
        "bump": "patch",
    })
    assert resp.status_code == 401


async def test_list_versions_initial(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.get(f"{API}/prompts/{prompt_id}/versions")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["version"] == "1.0.0"


async def test_list_versions_after_publish(client: AsyncClient, prompt_id: str) -> None:
    await client.post(f"{API}/prompts/{prompt_id}/publish", json={"bump": "patch"})

    resp = await client.get(f"{API}/prompts/{prompt_id}/versions")
    data = resp.json()["data"]
    assert len(data) == 2
    versions = {v["version"] for v in data}
    assert "1.0.0" in versions
    assert "1.0.1" in versions


async def test_get_specific_version(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.get(f"{API}/prompts/{prompt_id}/versions/1.0.0")
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] == "1.0.0"


async def test_get_version_not_found(client: AsyncClient, prompt_id: str) -> None:
    resp = await client.get(f"{API}/prompts/{prompt_id}/versions/9.9.9")
    assert resp.status_code == 404
