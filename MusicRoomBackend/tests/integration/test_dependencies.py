"""Tests that talk to real PostgreSQL and Redis.

Skipped by default in the unit run (``./test.sh`` deselects the ``integration``
marker). Run them against a live stack with ``./test.sh --docker --integration``
or, with the stack already up, ``docker compose exec api pytest -m integration``.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.redis import get_redis_client
from app.db.session import SessionLocal

pytestmark = pytest.mark.integration


async def test_postgres_answers_select_1() -> None:
    async with SessionLocal() as session:
        assert (await session.execute(text("SELECT 1"))).scalar_one() == 1


async def test_redis_answers_ping_and_roundtrips_a_key() -> None:
    client = get_redis_client()
    try:
        assert await client.ping() is True
        await client.set("musicroom:test:ping", "pong", ex=10)
        assert await client.get("musicroom:test:ping") == "pong"
    finally:
        await client.delete("musicroom:test:ping")
        await client.aclose()


async def test_health_reports_ok_against_the_real_stack(
    raw_client: AsyncClient,
) -> None:
    response = await raw_client.get("/health")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["database"] == "ok"
    assert body["redis"] == "ok"
