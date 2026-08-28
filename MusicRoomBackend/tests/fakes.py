"""In-memory stand-ins for the backing services.

Routes reach PostgreSQL and Redis only through the ``get_session`` and
``get_redis`` dependencies, and Spotify only through ``get_spotify``, so
overriding those with these fakes exercises the real routing, validation and
response models without a live stack. Grow them alongside the routes — a fake
that lags behind the real client is worse than no fake at all.
"""

from typing import Any

from sqlalchemy import inspect as sa_inspect

from app.core.spotify import (
    SpotifyNotConfigured,
    SpotifyResourceNotFound,
    SpotifyTrack,
    parse_ref,
)


def _identity(obj: Any) -> Any:
    """Primary-key value of a mapped instance, used as the store key."""
    values = tuple(getattr(obj, col.name, None) for col in sa_inspect(type(obj)).primary_key)
    return values[0] if len(values) == 1 else values


class FakeSession:
    """Stands in for ``AsyncSession`` with an in-memory identity map.

    Supports the slice the routes touch: ``execute`` (health check),
    ``add`` / ``flush`` / ``commit`` / ``get`` / ``delete`` (room + playlist
    writes), and ``scalars`` for the simple ``select(Model).where(col == value)
    .order_by(col)`` queries the playlist routes issue. ``commit`` moves added
    objects into the store keyed by ``(class name, primary key)``; ``delete``
    drops them. Set ``fail=True`` to make every operation raise, mimicking an
    unreachable database.
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

    async def flush(self, *args: Any, **kwargs: Any) -> None:
        self._guard()
        for obj in self.added:
            self._store[(type(obj).__name__, _identity(obj))] = obj
        self.added.clear()

    async def commit(self) -> None:
        self._guard()
        await self.flush()
        self.commits += 1

    async def delete(self, obj: Any) -> None:
        self._guard()
        self.deleted.append(obj)
        self._store.pop((type(obj).__name__, _identity(obj)), None)

    async def refresh(self, obj: Any, *args: Any, **kwargs: Any) -> None:
        self._guard()

    async def rollback(self) -> None:
        self.added.clear()

    async def get(self, entity: Any, ident: Any, *args: Any, **kwargs: Any) -> Any:
        self._guard()
        return self._store.get((entity.__name__, ident))

    async def scalars(self, statement: Any, *args: Any, **kwargs: Any) -> list[Any]:
        self._guard()
        entity = statement.column_descriptions[0]["entity"]
        rows = [obj for obj in self._store.values() if type(obj) is entity]
        where = statement.whereclause
        if where is not None:
            for clause in getattr(where, "clauses", [where]):
                column, value = clause.left.name, clause.right.value
                rows = [obj for obj in rows if getattr(obj, column, None) == value]
        for clause in statement._order_by_clauses:
            rows.sort(key=lambda obj, name=clause.name: getattr(obj, name))
        return rows


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


class FakeSpotify:
    """Stands in for ``app.core.spotify.SpotifyClient``.

    Holds canned playlists / tracks keyed by Spotify id (link parsing is the
    real thing). ``configured=False`` exercises the 503 path.
    """

    def __init__(self, *, configured: bool = True) -> None:
        self.configured = configured
        self.playlists: dict[str, list[SpotifyTrack]] = {}
        self.tracks: dict[str, SpotifyTrack] = {}

    async def fetch_playlist_tracks(self, ref: str) -> list[SpotifyTrack]:
        self._guard()
        key = parse_ref(ref, "playlist")
        try:
            return list(self.playlists[key])
        except KeyError:
            raise SpotifyResourceNotFound(f"no Spotify playlist {key}") from None

    async def fetch_track(self, ref: str) -> SpotifyTrack:
        self._guard()
        key = parse_ref(ref, "track")
        try:
            return self.tracks[key]
        except KeyError:
            raise SpotifyResourceNotFound(f"no Spotify track {key}") from None

    def _guard(self) -> None:
        if not self.configured:
            raise SpotifyNotConfigured("Spotify is not configured")
