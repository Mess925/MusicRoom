"""GET/POST /rooms/{room_id}/playlist — routing, Spotify error mapping, ordering."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.spotify import SpotifyTrack
from tests.fakes import FakeSpotify

PLAYLIST_ID = "3cEYpjA9oz9GiPac4AsH4n"
PLAYLIST_URL = f"https://open.spotify.com/playlist/{PLAYLIST_ID}"


def _track(n: str) -> SpotifyTrack:
    return SpotifyTrack(
        uri=f"spotify:track:{n}",
        track_id=n,
        title=f"Track {n}",
        artists=("Artist",),
        album="Album",
        duration_ms=200_000,
        artwork_url=None,
    )


async def _make_room(client: AsyncClient) -> str:
    return (await client.post("/rooms/public", json={})).json()["id"]


async def test_get_playlist_404_when_room_is_unknown(client: AsyncClient) -> None:
    response = await client.get(f"/rooms/{uuid.uuid4()}/playlist")
    assert response.status_code == 404


async def test_get_playlist_404_before_anything_is_imported(client: AsyncClient) -> None:
    room_id = await _make_room(client)
    response = await client.get(f"/rooms/{room_id}/playlist")
    assert response.status_code == 404
    assert response.json()["detail"] == "room has no playlist yet"


async def test_import_creates_the_playlist_with_ordered_tracks(
    client: AsyncClient, spotify: FakeSpotify
) -> None:
    room_id = await _make_room(client)
    spotify.playlists[PLAYLIST_ID] = [_track("a"), _track("b"), _track("c")]

    response = await client.post(
        f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["room_id"] == room_id
    assert body["source_url"] == PLAYLIST_URL
    assert [t["position"] for t in body["tracks"]] == [0, 1, 2]
    assert [t["spotify_track_id"] for t in body["tracks"]] == ["a", "b", "c"]
    assert body["tracks"][0]["artists"] == ["Artist"]


async def test_import_is_readable_back_with_get(client: AsyncClient, spotify: FakeSpotify) -> None:
    room_id = await _make_room(client)
    spotify.playlists[PLAYLIST_ID] = [_track("a"), _track("b")]

    await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})
    body = (await client.get(f"/rooms/{room_id}/playlist")).json()

    assert [t["spotify_track_id"] for t in body["tracks"]] == ["a", "b"]


async def test_import_replaces_by_default(client: AsyncClient, spotify: FakeSpotify) -> None:
    room_id = await _make_room(client)
    spotify.playlists[PLAYLIST_ID] = [_track("a"), _track("b")]
    await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})

    spotify.playlists[PLAYLIST_ID] = [_track("x")]
    body = (
        await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})
    ).json()

    assert [t["spotify_track_id"] for t in body["tracks"]] == ["x"]


async def test_import_with_replace_false_appends_and_dedupes(
    client: AsyncClient, spotify: FakeSpotify
) -> None:
    room_id = await _make_room(client)
    spotify.playlists[PLAYLIST_ID] = [_track("a"), _track("b")]
    await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})

    spotify.playlists[PLAYLIST_ID] = [_track("b"), _track("c")]  # "b" already present
    body = (
        await client.post(
            f"/rooms/{room_id}/playlist/import",
            json={"playlist_url": PLAYLIST_URL, "replace": False},
        )
    ).json()

    assert [t["spotify_track_id"] for t in body["tracks"]] == ["a", "b", "c"]
    assert [t["position"] for t in body["tracks"]] == [0, 1, 2]


async def test_import_503_when_spotify_is_not_configured(
    client: AsyncClient, spotify: FakeSpotify
) -> None:
    room_id = await _make_room(client)
    spotify.configured = False

    response = await client.post(
        f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL}
    )
    assert response.status_code == 503


async def test_import_422_on_a_non_spotify_url(client: AsyncClient) -> None:
    room_id = await _make_room(client)
    response = await client.post(
        f"/rooms/{room_id}/playlist/import", json={"playlist_url": "https://example.com/x"}
    )
    assert response.status_code == 422


async def test_import_404_when_spotify_has_no_such_playlist(client: AsyncClient) -> None:
    room_id = await _make_room(client)
    response = await client.post(
        f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL}
    )
    assert response.status_code == 404


async def test_import_missing_url_is_422(client: AsyncClient) -> None:
    room_id = await _make_room(client)
    assert (await client.post(f"/rooms/{room_id}/playlist/import", json={})).status_code == 422


async def test_add_track_creates_the_playlist_and_appends(
    client: AsyncClient, spotify: FakeSpotify
) -> None:
    room_id = await _make_room(client)
    spotify.tracks["4cOdK2wGLETKBW3PvgPWqT"] = _track("solo")

    response = await client.post(
        f"/rooms/{room_id}/playlist/tracks",
        json={"track_url": "spotify:track:4cOdK2wGLETKBW3PvgPWqT"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "position": 0,
        "spotify_uri": "spotify:track:solo",
        "spotify_track_id": "solo",
        "title": "Track solo",
        "artists": ["Artist"],
        "album": "Album",
        "duration_ms": 200_000,
        "artwork_url": None,
    }


async def test_add_track_appends_after_an_import(client: AsyncClient, spotify: FakeSpotify) -> None:
    room_id = await _make_room(client)
    spotify.playlists[PLAYLIST_ID] = [_track("a"), _track("b")]
    await client.post(f"/rooms/{room_id}/playlist/import", json={"playlist_url": PLAYLIST_URL})

    spotify.tracks["4cOdK2wGLETKBW3PvgPWqT"] = _track("c")
    added = (
        await client.post(
            f"/rooms/{room_id}/playlist/tracks",
            json={"track_url": "4cOdK2wGLETKBW3PvgPWqT"},
        )
    ).json()

    assert added["position"] == 2


async def test_add_duplicate_track_is_409(client: AsyncClient, spotify: FakeSpotify) -> None:
    room_id = await _make_room(client)
    spotify.tracks["4cOdK2wGLETKBW3PvgPWqT"] = _track("solo")
    url = {"track_url": "4cOdK2wGLETKBW3PvgPWqT"}
    await client.post(f"/rooms/{room_id}/playlist/tracks", json=url)

    assert (await client.post(f"/rooms/{room_id}/playlist/tracks", json=url)).status_code == 409


async def test_add_track_404_on_unknown_room(client: AsyncClient) -> None:
    response = await client.post(
        f"/rooms/{uuid.uuid4()}/playlist/tracks", json={"track_url": "4cOdK2wGLETKBW3PvgPWqT"}
    )
    assert response.status_code == 404


@pytest.mark.parametrize("path", ["import", "tracks"])
async def test_write_routes_reject_a_non_uuid_room_id(client: AsyncClient, path: str) -> None:
    key = "playlist_url" if path == "import" else "track_url"
    response = await client.post(f"/rooms/not-a-uuid/playlist/{path}", json={key: PLAYLIST_ID})
    assert response.status_code == 422
