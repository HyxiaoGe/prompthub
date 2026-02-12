import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Scene Test Project",
        "slug": f"scene-test-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


@pytest.fixture
async def prompt_id(client: AsyncClient, project_id: str) -> str:
    resp = await client.post(f"{API}/prompts", json={
        "name": "Scene Test Prompt",
        "slug": f"scene-prompt-{uuid.uuid4().hex[:8]}",
        "content": "Hello {{ name }}",
        "project_id": project_id,
        "variables": [{"name": "name", "type": "string", "required": True}],
    })
    return resp.json()["data"]["id"]


def _pipeline(prompt_id: str) -> dict:
    return {
        "steps": [
            {
                "id": "step-1",
                "prompt_ref": {"prompt_id": prompt_id},
                "variables": {},
            }
        ]
    }


async def test_create_scene(client: AsyncClient, project_id: str, prompt_id: str) -> None:
    resp = await client.post(f"{API}/scenes", json={
        "name": "My Scene",
        "slug": "my-scene",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["name"] == "My Scene"
    assert body["data"]["merge_strategy"] == "concat"


async def test_create_scene_nonexistent_prompt(client: AsyncClient, project_id: str) -> None:
    resp = await client.post(f"{API}/scenes", json={
        "name": "Bad Scene",
        "slug": "bad-scene",
        "project_id": project_id,
        "pipeline": _pipeline(str(uuid.uuid4())),
    })
    assert resp.status_code == 404


async def test_create_scene_invalid_pipeline(client: AsyncClient, project_id: str) -> None:
    resp = await client.post(f"{API}/scenes", json={
        "name": "Invalid",
        "slug": "invalid",
        "project_id": project_id,
        "pipeline": {"steps": "not-a-list"},
    })
    assert resp.status_code == 422


async def test_list_scenes_with_project_filter(
    client: AsyncClient, project_id: str, prompt_id: str,
) -> None:
    await client.post(f"{API}/scenes", json={
        "name": "Scene A",
        "slug": f"scene-a-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
    })
    resp = await client.get(f"{API}/scenes", params={"project_id": project_id})
    body = resp.json()
    assert body["code"] == 0
    assert body["meta"]["total"] >= 1


async def test_get_scene(client: AsyncClient, project_id: str, prompt_id: str) -> None:
    create_resp = await client.post(f"{API}/scenes", json={
        "name": "Get Me",
        "slug": f"get-me-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
    })
    scene_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"{API}/scenes/{scene_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == scene_id


async def test_get_scene_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/scenes/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_scene(client: AsyncClient, project_id: str, prompt_id: str) -> None:
    create_resp = await client.post(f"{API}/scenes", json={
        "name": "Old Name",
        "slug": f"update-me-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
    })
    scene_id = create_resp.json()["data"]["id"]

    resp = await client.put(f"{API}/scenes/{scene_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New Name"


async def test_create_scene_invalid_merge_strategy(
    client: AsyncClient, project_id: str, prompt_id: str,
) -> None:
    resp = await client.post(f"{API}/scenes", json={
        "name": "Bad Strategy",
        "slug": f"bad-strat-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
        "merge_strategy": "foobar",
    })
    assert resp.status_code == 422


async def test_delete_scene(client: AsyncClient, project_id: str, prompt_id: str) -> None:
    create_resp = await client.post(f"{API}/scenes", json={
        "name": "Delete Me",
        "slug": f"delete-me-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": _pipeline(prompt_id),
    })
    scene_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"{API}/scenes/{scene_id}")
    assert del_resp.status_code == 200

    get_resp = await client.get(f"{API}/scenes/{scene_id}")
    assert get_resp.status_code == 404
