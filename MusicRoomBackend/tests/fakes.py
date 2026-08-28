"""In-memory stand-ins for the backing services.

Routes reach PostgreSQL and Redis only through the ``get_session`` and
``get_redis`` dependencies, so overriding those with these fakes exercises the
real routing, validation and response models without a live stack. Grow them
alongside the routes — a fake that lags behind the real client is worse than no
fake at all.
"""

from typing import Any


class FakeSession:
    """Stands in for ``AsyncSession`` with an in-memory identity map.

    Supports the slice the routes touch: ``execute`` (health check), and
    ``add`` / ``commit`` / ``get`` / ``delete`` (room create, join, delete).
    ``commit`` moves added objects into the store keyed by ``(class name, id)``,
    so a create followed by a ``get`` in the same test round-trips; ``delete``
    drops the object from the store. Set ``fail=True`` to make every operation
    raise, mimicking an unreachable database.
    """

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.statements: list[str] = []
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.commits = 0
        self._store: dict[tuple[str, Any], Any] = {}

    def _guard(self) -> None:
        if self.fail:
            raise ConnectionError("database unreachable")

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        self.statements.append(str(statement))
        self._guard()
        return None

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self._guard()
        for obj in self.added:
            self._store[(type(obj).__name__, getattr(obj, "id", None))] = obj
        self.added.clear()
        self.commits += 1

    async def delete(self, obj: Any) -> None:
        self._guard()
        self.deleted.append(obj)
        self._store.pop((type(obj).__name__, getattr(obj, "id", None)), None)

    async def refresh(self, obj: Any, *args: Any, **kwargs: Any) -> None:
        self._guard()

    async def rollback(self) -> None:
        self.added.clear()

    async def get(self, entity: Any, ident: Any, *args: Any, **kwargs: Any) -> Any:
        self._guard()
        return self._store.get((entity.__name__, ident))


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
