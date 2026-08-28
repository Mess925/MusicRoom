"""Spotify Web API client.

The backend — not the iOS client — resolves Spotify playlist and track links, per
``REQUIREMENT.md`` §1 ("any external SDK ... only produces a token that the
backend verifies"). The client-credentials flow gives an app-only bearer token
(no user login), which is enough to read public playlist and track metadata.

``get_spotify`` is the FastAPI dependency; tests override it with
``tests.fakes.FakeSpotify``. One :class:`SpotifyClient` is built at import time
and shares a single ``httpx.AsyncClient`` pool, disposed by ``main.py``'s
lifespan.
"""

from __future__ import annotations

import re
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.core.config import settings

_AUTH_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"
_PAGE_SIZE = 100
_TIMEOUT = httpx.Timeout(10.0)

# A Spotify id is 22 base62 characters.
_BARE_ID = re.compile(r"\A[A-Za-z0-9]{22}\Z")


class SpotifyError(RuntimeError):
    """Base class for every Spotify-related failure."""


class SpotifyNotConfigured(SpotifyError):
    """No client id / secret is set on the server."""


class SpotifyAuthError(SpotifyError):
    """Spotify rejected our credentials or token."""


class InvalidSpotifyReference(SpotifyError):
    """A string is not a recognisable Spotify playlist / track reference."""


class SpotifyResourceNotFound(SpotifyError):
    """Spotify has no playlist / track with that id."""


def parse_ref(ref: str, kind: Literal["playlist", "track"]) -> str:
    """Pull the id out of a Spotify link, URI, or bare id.

    Accepts ``https://open.spotify.com/<kind>/<id>?...``, ``spotify:<kind>:<id>``
    and a bare 22-character id. Raises :class:`InvalidSpotifyReference` otherwise.
    """
    ref = ref.strip()
    if _BARE_ID.match(ref):
        return ref
    match = re.search(rf"{kind}[:/]([A-Za-z0-9]{{22}})", ref)
    if match is None:
        raise InvalidSpotifyReference(f"not a Spotify {kind} reference: {ref!r}")
    return match.group(1)


@dataclass(frozen=True, slots=True)
class SpotifyTrack:
    uri: str
    track_id: str
    title: str
    artists: tuple[str, ...]
    album: str | None
    duration_ms: int | None
    artwork_url: str | None

    @classmethod
    def from_api(cls, obj: dict[str, Any]) -> SpotifyTrack:
        album = obj.get("album") or {}
        images = album.get("images") or []
        return cls(
            uri=obj["uri"],
            track_id=obj["id"],
            title=obj["name"],
            artists=tuple(a["name"] for a in obj.get("artists", [])),
            album=album.get("name"),
            duration_ms=obj.get("duration_ms"),
            artwork_url=images[0]["url"] if images else None,
        )


class SpotifyClient:
    """Thin async wrapper over the Spotify Web API."""

    def __init__(self, client_id: str, client_secret: str, *, http: httpx.AsyncClient) -> None:
        self._id = client_id
        self._secret = client_secret
        self._http = http
        self._token: str | None = None
        self._token_expiry = 0.0

    @property
    def configured(self) -> bool:
        return bool(self._id and self._secret)

    async def fetch_track(self, ref: str) -> SpotifyTrack:
        track_id = parse_ref(ref, "track")
        return SpotifyTrack.from_api(await self._get(f"/tracks/{track_id}"))

    async def fetch_playlist_tracks(self, ref: str) -> list[SpotifyTrack]:
        playlist_id = parse_ref(ref, "playlist")
        tracks: list[SpotifyTrack] = []
        offset = 0
        while True:
            page = await self._get(
                f"/playlists/{playlist_id}/tracks",
                params={"limit": _PAGE_SIZE, "offset": offset},
            )
            items = page.get("items", [])
            for item in items:
                track = item.get("track")
                if track and track.get("id"):  # skip local / unavailable tracks
                    tracks.append(SpotifyTrack.from_api(track))
            if not items or page.get("next") is None:
                return tracks
            offset += len(items)

    async def _bearer(self) -> str:
        if self._token and time.monotonic() < self._token_expiry:
            return self._token
        if not self.configured:
            raise SpotifyNotConfigured("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET are not set")
        resp = await self._http.post(
            _AUTH_URL,
            data={"grant_type": "client_credentials"},
            auth=(self._id, self._secret),
        )
        if resp.status_code in (400, 401):
            raise SpotifyAuthError("Spotify rejected the client credentials")
        resp.raise_for_status()
        body = resp.json()
        token: str = body["access_token"]
        self._token = token
        self._token_expiry = time.monotonic() + body.get("expires_in", 3600) - 60
        return token

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = await self._bearer()
        resp = await self._http.get(
            f"{_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        if resp.status_code == 404:
            raise SpotifyResourceNotFound(f"no Spotify resource at {path}")
        if resp.status_code == 401:
            self._token = None
            raise SpotifyAuthError("Spotify token rejected")
        resp.raise_for_status()
        return resp.json()


_http_client = httpx.AsyncClient(timeout=_TIMEOUT)
spotify_client = SpotifyClient(
    settings.spotify_client_id,
    settings.spotify_client_secret,
    http=_http_client,
)


async def get_spotify() -> AsyncGenerator[SpotifyClient]:
    """FastAPI dependency yielding the shared Spotify client."""
    yield spotify_client


async def aclose() -> None:
    """Dispose the shared HTTP pool. Called from ``main.py``'s lifespan."""
    await _http_client.aclose()
