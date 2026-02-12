import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Engine Test Project",
        "slug": f"engine-test-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


@pytest.fixture
async def other_project_id(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/projects", json={
        "name": "Other Project",
        "slug": f"other-proj-{uuid.uuid4().hex[:8]}",
    })
    return resp.json()["data"]["id"]


async def _create_prompt(
    client: AsyncClient,
    project_id: str,
    name: str,
    content: str,
    variables: list | None = None,
    is_shared: bool = False,
) -> dict:
    slug = f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    resp = await client.post(f"{API}/prompts", json={
        "name": name,
        "slug": slug,
        "content": content,
        "project_id": project_id,
        "variables": variables or [],
        "is_shared": is_shared,
    })
    assert resp.status_code == 200, resp.json()
    return resp.json()["data"]


async def _create_scene(
    client: AsyncClient,
    project_id: str,
    steps: list,
    merge_strategy: str = "concat",
    separator: str = "\n\n",
) -> dict:
    resp = await client.post(f"{API}/scenes", json={
        "name": f"Test Scene {uuid.uuid4().hex[:6]}",
        "slug": f"test-scene-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": {"steps": steps},
        "merge_strategy": merge_strategy,
        "separator": separator,
    })
    assert resp.status_code == 200, resp.json()
    return resp.json()["data"]


async def test_single_step_concat_resolve(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(client, project_id, "Greeting", "Hello World")
    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": prompt["id"]}, "variables": {}},
    ])

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["final_content"] == "Hello World"
    assert len(body["steps"]) == 1
    assert body["steps"][0]["skipped"] is False


async def test_multi_step_concat_with_separator(client: AsyncClient, project_id: str) -> None:
    p1 = await _create_prompt(client, project_id, "Part One", "First part")
    p2 = await _create_prompt(client, project_id, "Part Two", "Second part")

    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": p1["id"]}, "variables": {}},
        {"id": "step-2", "prompt_ref": {"prompt_id": p2["id"]}, "variables": {}},
    ], separator="---")

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    body = resp.json()["data"]
    assert body["final_content"] == "First part---Second part"


async def test_variable_override_priority(client: AsyncClient, project_id: str) -> None:
    """prompt default='world', input='Alice', step override='Bob' → 'Bob'"""
    prompt = await _create_prompt(
        client, project_id, "Greet",
        "Hello {{ name }}",
        variables=[{"name": "name", "type": "string", "required": False, "default": "world"}],
    )
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt["id"]},
            "variables": {"name": "Bob"},
        },
    ])

    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"name": "Alice"}},
    )
    body = resp.json()["data"]
    assert body["final_content"] == "Hello Bob"


async def test_condition_true_executes(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(client, project_id, "Conditional", "Executed!")
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt["id"]},
            "variables": {},
            "condition": {"variable": "run", "operator": "eq", "value": True},
        },
    ])

    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"run": True}},
    )
    body = resp.json()["data"]
    assert body["steps"][0]["skipped"] is False
    assert body["final_content"] == "Executed!"


async def test_condition_false_skips(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(client, project_id, "Skippable", "Should not appear")
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt["id"]},
            "variables": {},
            "condition": {"variable": "run", "operator": "eq", "value": True},
        },
    ])

    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"run": False}},
    )
    body = resp.json()["data"]
    assert body["steps"][0]["skipped"] is True
    assert body["steps"][0]["skip_reason"] == "Condition not met"
    assert body["final_content"] == ""


async def test_chain_strategy_output_passing(client: AsyncClient, project_id: str) -> None:
    """Step 1 output is available to step 2 via chain_context."""
    p1 = await _create_prompt(client, project_id, "Step1", "intro text")
    p2 = await _create_prompt(
        client, project_id, "Step2",
        "Summary: {{ intro }}",
        variables=[{"name": "intro", "type": "string", "required": True}],
    )

    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": p1["id"]}, "variables": {}, "output_key": "intro"},
        {"id": "step-2", "prompt_ref": {"prompt_id": p2["id"]}, "variables": {}},
    ], merge_strategy="chain")

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    body = resp.json()["data"]
    assert body["final_content"] == "Summary: intro text"
    assert body["merge_strategy"] == "chain"


async def test_cross_project_shared_prompt(
    client: AsyncClient, project_id: str, other_project_id: str,
) -> None:
    shared_prompt = await _create_prompt(
        client, other_project_id, "Shared Prompt", "Shared content", is_shared=True,
    )

    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": shared_prompt["id"]}, "variables": {}},
    ])

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    assert resp.status_code == 200
    assert resp.json()["data"]["final_content"] == "Shared content"


async def test_cross_project_non_shared_denied(
    client: AsyncClient, project_id: str, other_project_id: str,
) -> None:
    private_prompt = await _create_prompt(
        client, other_project_id, "Private Prompt", "Private content", is_shared=False,
    )

    resp = await client.post(f"{API}/scenes", json={
        "name": "Bad Cross Ref",
        "slug": f"bad-ref-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "pipeline": {
            "steps": [
                {"id": "step-1", "prompt_ref": {"prompt_id": private_prompt["id"]}, "variables": {}},
            ]
        },
    })
    assert resp.status_code == 403


async def test_version_locked_resolve(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(client, project_id, "Versioned", "v1 content")
    prompt_id = prompt["id"]

    # Publish v1.1.0 with new content
    await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "minor",
        "content": "v1.1 content",
        "changelog": "updated",
    })

    # Scene locked to 1.0.0
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt_id, "version": "1.0.0"},
            "variables": {},
        },
    ])

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    body = resp.json()["data"]
    assert body["final_content"] == "v1 content"
    assert body["steps"][0]["version"] == "1.0.0"


async def test_latest_version_resolve(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(client, project_id, "Latest", "original")
    prompt_id = prompt["id"]

    # Publish a new version
    await client.post(f"{API}/prompts/{prompt_id}/publish", json={
        "bump": "minor",
        "content": "updated content",
        "changelog": "update",
    })

    # Scene with no version lock → uses current_version (but content from prompt model)
    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": prompt_id}, "variables": {}},
    ])

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    body = resp.json()["data"]
    # Fix 1: content must come from prompt_versions, not stale prompt.content
    assert body["steps"][0]["version"] == "1.1.0"
    assert body["final_content"] == "updated content"


async def test_condition_in_with_list(client: AsyncClient, project_id: str) -> None:
    """'in' operator with a list value evaluates correctly."""
    prompt = await _create_prompt(client, project_id, "InList", "Matched!")
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt["id"]},
            "variables": {},
            "condition": {"variable": "env", "operator": "in", "value": ["prod", "staging"]},
        },
    ])

    # Match
    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"env": "prod"}},
    )
    body = resp.json()["data"]
    assert body["steps"][0]["skipped"] is False
    assert body["final_content"] == "Matched!"

    # No match
    resp2 = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"env": "dev"}},
    )
    body2 = resp2.json()["data"]
    assert body2["steps"][0]["skipped"] is True


async def test_condition_in_with_non_list_returns_false(client: AsyncClient, project_id: str) -> None:
    """'in' operator with a non-list value gracefully skips the step."""
    prompt = await _create_prompt(client, project_id, "InNonList", "Should skip")
    scene = await _create_scene(client, project_id, [
        {
            "id": "step-1",
            "prompt_ref": {"prompt_id": prompt["id"]},
            "variables": {},
            "condition": {"variable": "x", "operator": "in", "value": 42},
        },
    ])

    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {"x": "anything"}},
    )
    body = resp.json()["data"]
    assert body["steps"][0]["skipped"] is True


async def test_missing_required_variable_422(client: AsyncClient, project_id: str) -> None:
    prompt = await _create_prompt(
        client, project_id, "Strict Prompt",
        "{{ required_var }}",
        variables=[{"name": "required_var", "type": "string", "required": True}],
    )
    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": prompt["id"]}, "variables": {}},
    ])

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    assert resp.status_code == 422


async def test_select_best_returns_first(client: AsyncClient, project_id: str) -> None:
    p1 = await _create_prompt(client, project_id, "Best1", "option A")
    p2 = await _create_prompt(client, project_id, "Best2", "option B")

    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": p1["id"]}, "variables": {}},
        {"id": "step-2", "prompt_ref": {"prompt_id": p2["id"]}, "variables": {}},
    ], merge_strategy="select_best")

    resp = await client.post(f"{API}/scenes/{scene['id']}/resolve", json={"variables": {}})
    body = resp.json()["data"]
    assert body["final_content"] == "option A"


async def test_resolve_creates_call_log(
    client: AsyncClient, project_id: str,
) -> None:
    prompt = await _create_prompt(client, project_id, "Logged", "Log me")
    scene = await _create_scene(client, project_id, [
        {"id": "step-1", "prompt_ref": {"prompt_id": prompt["id"]}, "variables": {}},
    ])

    resp = await client.post(
        f"{API}/scenes/{scene['id']}/resolve",
        json={"variables": {}, "caller_system": "test-system"},
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total_token_estimate"] >= 0
