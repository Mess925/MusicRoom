"""Integration-only fixtures.

The engine and Redis pool in ``app.db.session`` / ``app.core.redis`` are module
level singletons bound to the loop that first uses them, which is why the whole
suite shares one event loop (``asyncio_default_test_loop_scope = "session"``).
This closes them inside that loop instead of leaving it to the garbage
collector at interpreter shutdown.
"""

from collections.abc import AsyncIterator

import pytest

from app.core.redis import pool
from app.db.session import engine


@pytest.fixture(scope="session", autouse=True)
async def close_real_connections() -> AsyncIterator[None]:
    yield
    await engine.dispose()
    await pool.aclose()
