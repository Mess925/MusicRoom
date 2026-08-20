"""Shared fixtures for the whole suite.

Environment variables are set **before** anything under ``app`` is imported,
because ``app.core.config`` builds a cached ``Settings`` instance at import
time. Real environment variables take precedence over ``.env``, so this pins
the values the tests assert on regardless of the developer's local ``.env``.
"""

import os
from collections.abc import AsyncIterator, Callable, Iterator

TEST_ENV = {
    "APP_NAME": "Music Room API Test",
    "API_VERSION": "9.9.9",
    "ENVIRONMENT": "test",
    "DEBUG": "false",
    "DOCS_ENABLED": "true",
}
os.environ.update(TEST_ENV)

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.redis import get_redis
from app.db.session import get_session
from app.main import app as fastapi_app
from tests.fakes import FakeRedis, FakeSession

Override = Callable[..., None]


@pytest.fixture
def app() -> Iterator[FastAPI]:
    """The real application, with dependency overrides cleared afterwards."""
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def session() -> FakeSession:
    """A healthy fake database session, inspectable after the request."""
    return FakeSession()


@pytest.fixture
def redis() -> FakeRedis:
    """A healthy fake Redis client, inspectable after the request."""
    return FakeRedis()


@pytest.fixture
def override(app: FastAPI) -> Override:
    """Point ``get_session`` / ``get_redis`` at specific fakes.

    Usage::

        override(session=FakeSession(fail=True))
    """

    def _override(
        *,
        session: FakeSession | None = None,
        redis: FakeRedis | None = None,
    ) -> None:
        if session is not None:
            app.dependency_overrides[get_session] = lambda: session
        if redis is not None:
            app.dependency_overrides[get_redis] = lambda: redis

    return _override


@pytest.fixture
async def client(
    app: FastAPI,
    session: FakeSession,
    redis: FakeRedis,
    override: Override,
) -> AsyncIterator[AsyncClient]:
    """HTTP client wired to the app in-process, with healthy fake backends.

    No sockets, no Postgres, no Redis. Tests needing a failing dependency call
    ``override(...)`` before issuing the request — the later override wins.
    """
    override(session=session, redis=redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def raw_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client with **no** dependency overrides — real Postgres/Redis wiring.

    Only for tests marked ``integration``.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
