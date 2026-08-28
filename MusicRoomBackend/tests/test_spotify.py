"""app.core.spotify — link parsing, metadata mapping, token reuse, error mapping."""

import httpx
import pytest

from app.core.spotify import (
    InvalidSpotifyReference,
    SpotifyAuthError,
    SpotifyClient,
    SpotifyNotConfigured,
    SpotifyResourceNotFound,
    SpotifyTrack,
    parse_ref,
)

_ID = "3cEYpjA9oz9GiPac4AsH4n"


@pytest.mark.parametrize(
    "ref",
    [
        _ID,
        f"  {_ID}  ",
        f"https://open.spotify.com/playlist/{_ID}",
        f"https://open.spotify.com/playlist/{_ID}?si=abc123",
        f"spotify:playlist:{_ID}",
    ],
)
def test_parse_ref_pulls_the_id(ref: str) -> None:
    assert parse_ref(ref, "playlist") == _ID


@pytest.mark.parametrize("ref", ["", "not a url", "https://open.spotify.com/track/" + _ID])
def test_parse_ref_rejects_the_wrong_kind_or_junk(ref: str) -> None:
    with pytest.raises(InvalidSpotifyReference):
        parse_ref(ref, "playlist")


def test_track_from_api_maps_the_fields() -> None:
    track = SpotifyTrack.from_api(
        {
            "uri": "spotify:track:abc",
            "id": "abc",
            "name": "Song",
            "artists": [{"name": "A"}, {"name": "B"}],
            "album": {"name": "Album", "images": [{"url": "http://img/large"}, {"url": "small"}]},
            "duration_ms": 1000,
        }
    )
    assert track == SpotifyTrack(
        uri="spotify:track:abc",
        track_id="abc",
        title="Song",
        artists=("A", "B"),
        album="Album",
        duration_ms=1000,
        artwork_url="http://img/large",
    )


def test_track_from_api_tolerates_a_missing_album() -> None:
    track = SpotifyTrack.from_api(
        {"uri": "u", "id": "i", "name": "n", "artists": [], "duration_ms": None}
    )
    assert track.album is None
    assert track.artwork_url is None
    assert track.artists == ()


def _client(handler: httpx.MockTransport, **kw: str) -> SpotifyClient:
    kw.setdefault("client_id", "id")
    kw.setdefault("client_secret", "secret")
    return SpotifyClient(
        kw["client_id"], kw["client_secret"], http=httpx.AsyncClient(transport=handler)
    )


async def test_not_configured_raises_before_any_request() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:  # pragma: no cover - never called
        raise AssertionError("should not reach the network")

    client = _client(httpx.MockTransport(handler), client_id="", client_secret="")
    with pytest.raises(SpotifyNotConfigured):
        await client.fetch_track("0000000000000000000000")
    await client._http.aclose()


async def test_fetch_track_authenticates_once_then_reuses_the_token() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path == "/api/token":
            return httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
        assert request.headers["Authorization"] == "Bearer T"
        return httpx.Response(
            200,
            json={
                "uri": "spotify:track:t",
                "id": "t",
                "name": "Name",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Al", "images": []},
                "duration_ms": 200,
            },
        )

    client = _client(httpx.MockTransport(handler))
    first = await client.fetch_track("spotify:track:0000000000000000000000")
    second = await client.fetch_track("1111111111111111111111")
    await client._http.aclose()

    assert first.title == "Name" and second.title == "Name"
    assert sum(url.endswith("/api/token") for url in calls) == 1


async def test_fetch_playlist_tracks_follows_pagination_and_skips_empty_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            return httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
        offset = int(request.url.params.get("offset", "0"))
        if offset == 0:
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"track": {"uri": "u1", "id": "1", "name": "one", "artists": []}},
                        {"track": None},
                    ],
                    "next": "https://api.spotify.com/v1/playlists/x/tracks?offset=2",
                },
            )
        return httpx.Response(
            200,
            json={
                "items": [{"track": {"uri": "u2", "id": "2", "name": "two", "artists": []}}],
                "next": None,
            },
        )

    client = _client(httpx.MockTransport(handler))
    tracks = await client.fetch_playlist_tracks("spotify:playlist:0000000000000000000000")
    await client._http.aclose()

    assert [t.track_id for t in tracks] == ["1", "2"]


async def test_404_maps_to_resource_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            return httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
        return httpx.Response(404, json={"error": {"status": 404}})

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(SpotifyResourceNotFound):
        await client.fetch_track("0000000000000000000000")
    await client._http.aclose()


async def test_rejected_credentials_map_to_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(SpotifyAuthError):
        await client.fetch_track("0000000000000000000000")
    await client._http.aclose()
