import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Prompt Test Project",
        "slug": f"prompt-test-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


async def test_create_prompt(client: AsyncClient, project_id: str) -> None:
    resp = await client.post(f"{API}/prompts", json={
        "name": "My Prompt",
        "slug": "my-prompt",
        "content": "Hello {{ name }}",
        "project_id": project_id,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["name"] == "My Prompt"
    assert data["current_version"] == "1.0.0"
    assert data["created_by"] is not None


async def test_create_prompt_duplicate_slug(client: AsyncClient, project_id: str) -> None:
    await client.post(f"{API}/prompts", json={
        "name": "First",
        "slug": "dup-prompt",
        "content": "v1",
        "project_id": project_id,
    })
    resp = await client.post(f"{API}/prompts", json={
        "name": "Second",
        "slug": "dup-prompt",
        "content": "v2",
        "project_id": project_id,
    })
    assert resp.status_code == 409


async def test_create_prompt_invalid_project(client: AsyncClient) -> None:
    fake_id = uuid.uuid4()
    resp = await client.post(f"{API}/prompts", json={
        "name": "Orphan",
        "slug": "orphan",
        "content": "text",
        "project_id": str(fake_id),
    })
    assert resp.status_code == 404


async def test_create_prompt_no_auth(unauthed_client: AsyncClient) -> None:
    resp = await unauthed_client.post(f"{API}/prompts", json={
        "name": "No Auth",
        "slug": "no-auth",
        "content": "text",
        "project_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 401


async def test_list_prompts(client: AsyncClient, project_id: str) -> None:
    await client.post(f"{API}/prompts", json={
        "name": "List A",
        "slug": "list-a",
        "content": "a",
        "project_id": project_id,
    })
    await client.post(f"{API}/prompts", json={
        "name": "List B",
        "slug": "list-b",
        "content": "b",
        "project_id": project_id,
    })

    resp = await client.get(f"{API}/prompts", params={"project_id": project_id})
    body = resp.json()
    assert body["meta"]["total"] == 2


async def test_list_prompts_filter_by_project(client: AsyncClient) -> None:
    p1 = (await client.post(f"{API}/projects", json={
        "name": "Filter P1",
        "slug": f"filter-p1-{uuid.uuid4().hex[:8]}",
    })).json()["data"]["id"]

    p2 = (await client.post(f"{API}/projects", json={
        "name": "Filter P2",
        "slug": f"filter-p2-{uuid.uuid4().hex[:8]}",
    })).json()["data"]["id"]

    await client.post(f"{API}/prompts", json={
        "name": "In P1",
        "slug": "in-p1",
        "content": "x",
        "project_id": p1,
    })
    await client.post(f"{API}/prompts", json={
        "name": "In P2",
        "slug": "in-p2",
        "content": "y",
        "project_id": p2,
    })

    resp = await client.get(f"{API}/prompts", params={"project_id": p1})
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["slug"] == "in-p1"


async def test_list_prompts_search(client: AsyncClient, project_id: str) -> None:
    await client.post(f"{API}/prompts", json={
        "name": "Image Generator",
        "slug": "image-gen",
        "content": "generate images",
        "project_id": project_id,
    })
    await client.post(f"{API}/prompts", json={
        "name": "Text Writer",
        "slug": "text-writer",
        "content": "write text",
        "project_id": project_id,
    })

    resp = await client.get(f"{API}/prompts", params={"search": "Image", "project_id": project_id})
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["slug"] == "image-gen"


async def test_get_prompt(client: AsyncClient, project_id: str) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Get Me",
        "slug": "get-me",
        "content": "hello",
        "project_id": project_id,
    })
    prompt_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"{API}/prompts/{prompt_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["slug"] == "get-me"


async def test_get_prompt_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/prompts/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_prompt(client: AsyncClient, project_id: str) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Old Name",
        "slug": "update-me",
        "content": "old content",
        "project_id": project_id,
    })
    prompt_id = create_resp.json()["data"]["id"]

    resp = await client.put(f"{API}/prompts/{prompt_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New Name"


async def test_update_prompt_not_found(client: AsyncClient) -> None:
    resp = await client.put(f"{API}/prompts/{uuid.uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


async def test_delete_prompt(client: AsyncClient, project_id: str) -> None:
    create_resp = await client.post(f"{API}/prompts", json={
        "name": "Delete Me",
        "slug": "delete-me",
        "content": "bye",
        "project_id": project_id,
    })
    prompt_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"{API}/prompts/{prompt_id}")
    assert del_resp.status_code == 200

    get_resp = await client.get(f"{API}/prompts/{prompt_id}")
    assert get_resp.status_code == 404


async def test_delete_prompt_not_found(client: AsyncClient) -> None:
    resp = await client.delete(f"{API}/prompts/{uuid.uuid4()}")
    assert resp.status_code == 404
