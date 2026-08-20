"""GET /health — dependency readiness roll-up."""

from httpx import AsyncClient

from app.core.config import settings
from tests.fakes import FakeRedis, FakeSession


async def test_health_ok_when_both_dependencies_answer(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.api_version,
        "environment": settings.environment,
        "database": "ok",
        "redis": "ok",
    }


async def test_health_pings_each_dependency_once(
    client: AsyncClient, session: FakeSession, redis: FakeRedis
) -> None:
    await client.get("/health")

    assert session.statements == ["SELECT 1"]
    assert redis.pings == 1


async def test_health_503_when_database_is_down(client: AsyncClient, override) -> None:
    override(session=FakeSession(fail=True))

    response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "error"
    assert body["redis"] == "ok"


async def test_health_503_when_redis_is_down(client: AsyncClient, override) -> None:
    override(redis=FakeRedis(fail=True))

    response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "ok"
    assert body["redis"] == "error"


async def test_health_503_when_everything_is_down(client: AsyncClient, override) -> None:
    override(session=FakeSession(fail=True), redis=FakeRedis(fail=True))

    response = await client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"


async def test_health_never_leaks_extra_fields(client: AsyncClient) -> None:
    """The response model is the contract — keep it exact."""
    assert set((await client.get("/health")).json()) == {
        "status",
        "service",
        "version",
        "environment",
        "database",
        "redis",
    }
