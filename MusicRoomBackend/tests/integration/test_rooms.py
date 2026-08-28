"""Room create + join against real PostgreSQL.

Needs the ``rooms`` table — run ``alembic upgrade head`` against the stack first.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.db.session import SessionLocal

pytestmark = pytest.mark.integration


async def _delete(room_id: str) -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM rooms WHERE id = :id"), {"id": room_id})
        await session.commit()


async def test_public_room_round_trips(raw_client: AsyncClient) -> None:
    created = (await raw_client.post("/rooms/public", json={"name": "lobby"})).json()
    try:
        assert created["access_code"] is None

        joined = await raw_client.post(f"/rooms/{created['id']}/join")
        assert joined.status_code == 200
        assert joined.json()["name"] == "lobby"
    finally:
        await _delete(created["id"])


async def test_private_room_requires_its_generated_code(raw_client: AsyncClient) -> None:
    created = (await raw_client.post("/rooms/private", json={})).json()
    try:
        assert created["access_code"]

        assert (await raw_client.post(f"/rooms/{created['id']}/join")).status_code == 403
        ok = await raw_client.post(
            f"/rooms/{created['id']}/join", json={"access_code": created["access_code"]}
        )
        assert ok.status_code == 200
    finally:
        await _delete(created["id"])
