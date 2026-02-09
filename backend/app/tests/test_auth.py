import pytest
from httpx import AsyncClient


@pytest.fixture
def api_prefix() -> str:
    return "/api/v1"


async def test_no_auth_header_returns_401(unauthed_client: AsyncClient, api_prefix: str) -> None:
    resp = await unauthed_client.get(f"{api_prefix}/projects")
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == 40100


async def test_invalid_api_key_returns_401(unauthed_client: AsyncClient, api_prefix: str) -> None:
    resp = await unauthed_client.get(
        f"{api_prefix}/projects",
        headers={"Authorization": "Bearer invalid-key-000000"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == 40100


async def test_valid_api_key_returns_200(client: AsyncClient, api_prefix: str) -> None:
    resp = await client.get(f"{api_prefix}/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


async def test_health_endpoint_no_auth_required(unauthed_client: AsyncClient) -> None:
    resp = await unauthed_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["status"] == "healthy"
