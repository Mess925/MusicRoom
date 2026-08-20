"""In-memory stand-ins for the backing services.

Routes reach PostgreSQL and Redis only through the ``get_session`` and
``get_redis`` dependencies, so overriding those with these fakes exercises the
real routing, validation and response models without a live stack. Grow them
alongside the routes — a fake that lags behind the real client is worse than no
fake at all.
"""

from typing import Any


class FakeSession:
    """Stands in for ``AsyncSession``: records statements, optionally fails.

    Only ``execute`` is implemented — that is all the current routes use.
    """

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.statements: list[str] = []

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        self.statements.append(str(statement))
        if self.fail:
            raise ConnectionError("database unreachable")
        return None


class FakeRedis:
    """Stands in for ``redis.asyncio.Redis`` with an in-memory string store."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.pings = 0
        self.store: dict[str, str] = {}

    async def ping(self) -> bool:
        self.pings += 1
        if self.fail:
            raise ConnectionError("redis unreachable")
        return True

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError("redis unreachable")
        return self.store.get(key)

    async def set(self, key: str, value: str, **kwargs: Any) -> bool:
        if self.fail:
            raise ConnectionError("redis unreachable")
        self.store[key] = value
        return True

    async def aclose(self) -> None:
        return None
