"""Playlist import + add-track against real PostgreSQL.

Needs the ``playlists`` / ``playlist_tracks`` tables — run ``alembic upgrade
head`` against the stack first. Spotify itself is faked (no credentials in CI);
the database is real, so this covers the ORM writes, ordering, and the
``rooms`` -> ``playlists`` -> ``playlist_tracks`` delete cascade.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.spotify import SpotifyTrack, get_spotify
from app.db.session import SessionLocal
from app.main import app
from tests.fakes import FakeSpotify

pytestmark = pytest.mark.integration

PLAYLIST_ID = "3cEYpjA9oz9GiPac4AsH4n"
PLAYLIST_URL = f"https://open.spotify.com/playlist/{PLAYLIST_ID}"
TRACK_ID = "4cOdK2wGLETKBW3PvgPWqT"


def _track(n: str) -> SpotifyTrack:
    return SpotifyTrack(
        uri=f"spotify:track:{n}",
        track_id=n,
        title=f"Track {n}",
        artists=("Artist One", "Artist Two"),
        album="Album",
        duration_ms=210_000,
        artwork_url=f"https://img/{n}",
    )


@pytest.fixture
def spotify() -> FakeSpotify:
    fake = FakeSpotify()
    fake.playlists[PLAYLIST_ID] = [_track("a"), _track("b")]
    fake.tracks[TRACK_ID] = _track("solo")
    return fake


@pytest.fixture
async def client(spotify: FakeSpotify):
    app.dependency_overrides[get_spotify] = lambda: spotify
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


async def _row_count(table: str, room_id: str) -> int:
    column = "room_id" if table == "playlists" else "playlist_id"
    async with SessionLocal() as session:
        result = await session.execute(
            text(f"SELECT count(*) FROM {table} WHERE {column} = :id"), {"id": room_id}
        )
        return result.scalar_one()


async def _delete_room(client: AsyncClient, room_id: str) -> None:
    await client.request("DELETE", f"/rooms/{room_id}", json={"confirmation_code": room_id})


async def test_import_persists_tracks_in_order(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={"name": "lobby"})).json()["id"]
    try:
        imported = await client.post(
            f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL}
        )
        assert imported.status_code == 201

        body = (await client.get(f"/rooms/{room_id}/playlist")).json()
        assert body["source_url"] == PLAYLIST_URL
        assert [t["position"] for t in body["tracks"]] == [0, 1]
        assert [t["spotify_track_id"] for t in body["tracks"]] == ["a", "b"]
        assert body["tracks"][0]["artists"] == ["Artist One", "Artist Two"]
    finally:
        await _delete_room(client, room_id)


async def test_import_replace_swaps_the_track_set(
    client: AsyncClient, spotify: FakeSpotify
) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]
    try:
        await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})
        spotify.playlists[PLAYLIST_ID] = [_track("c")]
        body = (
            await client.post(
                f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL}
            )
        ).json()
        assert [t["spotify_track_id"] for t in body["tracks"]] == ["c"]
        assert await _row_count("playlist_tracks", room_id) == 1
    finally:
        await _delete_room(client, room_id)


async def test_add_track_then_get(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]
    try:
        added = await client.post(
            f"/rooms/{room_id}/playlist/tracks", json={"track_url": f"spotify:track:{TRACK_ID}"}
        )
        assert added.status_code == 201
        assert added.json()["position"] == 0

        dup = await client.post(f"/rooms/{room_id}/playlist/tracks", json={"track_url": TRACK_ID})
        assert dup.status_code == 409
    finally:
        await _delete_room(client, room_id)


async def test_deleting_the_room_cascades_to_playlist_and_tracks(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]
    await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})
    assert await _row_count("playlist_tracks", room_id) == 2

    await _delete_room(client, room_id)

    assert await _row_count("playlists", room_id) == 0
    assert await _row_count("playlist_tracks", room_id) == 0


async def test_get_playlist_unknown_room_is_404(client: AsyncClient) -> None:
    assert (
        await client.get("/rooms/00000000-0000-0000-0000-000000000000/playlist")
    ).status_code == 404
