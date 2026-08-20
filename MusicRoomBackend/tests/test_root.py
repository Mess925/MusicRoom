"""GET / — the service banner."""

from httpx import AsyncClient

from app.core.config import settings


async def test_root_returns_service_identity(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": settings.app_name,
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": settings.docs_url,
        "redoc": settings.redoc_url,
        "openapi": settings.openapi_url,
    }


async def test_root_uses_test_settings(client: AsyncClient) -> None:
    """conftest pins the env, so the banner is deterministic."""
    body = (await client.get("/")).json()

    assert body["environment"] == "test"
    assert body["version"] == "9.9.9"


async def test_root_touches_no_backends(client: AsyncClient, session, redis) -> None:
    await client.get("/")

    assert session.statements == []
    assert redis.pings == 0
