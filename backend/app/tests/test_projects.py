import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


async def test_create_project(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/projects", json={
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["name"] == "Test Project"
    assert data["slug"] == "test-project"
    assert data["created_by"] is not None


async def test_create_project_duplicate_slug(client: AsyncClient) -> None:
    await client.post(f"{API}/projects", json={
        "name": "Project A",
        "slug": "dup-slug",
    })
    resp = await client.post(f"{API}/projects", json={
        "name": "Project B",
        "slug": "dup-slug",
    })
    assert resp.status_code == 409
    assert resp.json()["code"] == 40900


async def test_create_project_invalid_slug(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/projects", json={
        "name": "Bad Slug",
        "slug": "Bad_Slug!",
    })
    assert resp.status_code == 422


async def test_create_project_no_auth(unauthed_client: AsyncClient) -> None:
    resp = await unauthed_client.post(f"{API}/projects", json={
        "name": "No Auth",
        "slug": "no-auth",
    })
    assert resp.status_code == 401


async def test_list_projects_returns_ok(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert "total" in body["meta"]


async def test_list_projects_with_data(client: AsyncClient) -> None:
    baseline = (await client.get(f"{API}/projects")).json()["meta"]["total"]

    await client.post(f"{API}/projects", json={"name": "P1", "slug": "p-one"})
    await client.post(f"{API}/projects", json={"name": "P2", "slug": "p-two"})

    resp = await client.get(f"{API}/projects")
    body = resp.json()
    assert body["meta"]["total"] == baseline + 2


async def test_list_projects_pagination(client: AsyncClient) -> None:
    baseline = (await client.get(f"{API}/projects")).json()["meta"]["total"]

    for i in range(3):
        await client.post(f"{API}/projects", json={"name": f"P{i}", "slug": f"page-{i}"})

    total = baseline + 3
    resp = await client.get(f"{API}/projects", params={"page": 1, "page_size": 2})
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == total
    assert body["meta"]["page"] == 1


async def test_get_project_detail(client: AsyncClient) -> None:
    create_resp = await client.post(f"{API}/projects", json={
        "name": "Detail Project",
        "slug": "detail-proj",
    })
    project_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"{API}/projects/{project_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["name"] == "Detail Project"
    assert body["data"]["prompt_count"] == 0
    assert body["data"]["scene_count"] == 0


async def test_get_project_not_found(client: AsyncClient) -> None:
    fake_id = uuid.uuid4()
    resp = await client.get(f"{API}/projects/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["code"] == 40400


async def test_list_project_prompts(client: AsyncClient) -> None:
    proj_resp = await client.post(f"{API}/projects", json={
        "name": "Prompt Project",
        "slug": "prompt-proj",
    })
    project_id = proj_resp.json()["data"]["id"]

    await client.post(f"{API}/prompts", json={
        "name": "Prompt A",
        "slug": "prompt-a",
        "content": "Hello",
        "project_id": project_id,
    })

    resp = await client.get(f"{API}/projects/{project_id}/prompts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["slug"] == "prompt-a"
