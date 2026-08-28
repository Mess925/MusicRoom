"""Building a room's playlist from Spotify.

The backend resolves every Spotify link itself (client-credentials flow) — the
iOS client only forwards the URL the user pasted or the track they picked.

* ``GET  /rooms/{room_id}/playlist``        — the room's playlist and its tracks.
* ``POST /rooms/{room_id}/playlist/import`` — import a whole Spotify playlist by link.
* ``POST /rooms/{room_id}/playlist/tracks`` — append one Spotify track by link.

No owner check yet — that waits for real auth. Any caller who knows the room id
can edit its playlist.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.spotify import (
    InvalidSpotifyReference,
    SpotifyClient,
    SpotifyError,
    SpotifyNotConfigured,
    SpotifyResourceNotFound,
    SpotifyTrack,
    get_spotify,
)
from app.db.session import get_session
from app.models.playlist import Playlist, PlaylistEditTier, PlaylistTrack, PlaylistVisibility
from app.models.room import Room
from app.schemas.playlist import (
    PlaylistDetail,
    PlaylistImportRequest,
    PlaylistTrackDetail,
    TrackAddRequest,
)

router = APIRouter(prefix="/rooms/{room_id}/playlist", tags=["playlists"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SpotifyDep = Annotated[SpotifyClient, Depends(get_spotify)]


async def _require_room(session: AsyncSession, room_id: uuid.UUID) -> Room:
    room = await session.get(Room, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="room not found")
    return room


async def _load_tracks(session: AsyncSession, room_id: uuid.UUID) -> list[PlaylistTrack]:
    result = await session.scalars(
        select(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == room_id)
        .order_by(PlaylistTrack.position)
    )
    return list(result)


def _new_playlist(room_id: uuid.UUID, source_url: str | None) -> Playlist:
    return Playlist(
        room_id=room_id,
        name=None,
        visibility=PlaylistVisibility.PUBLIC.value,
        edit_tier=PlaylistEditTier.EVERYONE.value,
        source_url=source_url,
    )


def _track_row(room_id: uuid.UUID, position: int, track: SpotifyTrack) -> PlaylistTrack:
    return PlaylistTrack(
        id=uuid.uuid4(),
        playlist_id=room_id,
        position=position,
        spotify_uri=track.uri,
        spotify_track_id=track.track_id,
        title=track.title,
        artists=list(track.artists),
        album=track.album,
        duration_ms=track.duration_ms,
        artwork_url=track.artwork_url,
    )


def _detail(playlist: Playlist, tracks: list[PlaylistTrack]) -> PlaylistDetail:
    return PlaylistDetail(
        room_id=playlist.room_id,
        name=playlist.name,
        visibility=PlaylistVisibility(playlist.visibility),
        edit_tier=PlaylistEditTier(playlist.edit_tier),
        source_url=playlist.source_url,
        tracks=[PlaylistTrackDetail.model_validate(track) for track in tracks],
    )


def _spotify_error(exc: SpotifyError) -> HTTPException:
    if isinstance(exc, SpotifyNotConfigured):
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spotify integration is not configured on the server",
        )
    if isinstance(exc, InvalidSpotifyReference):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    if isinstance(exc, SpotifyResourceNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Spotify request failed")


@router.get(
    "",
    response_model=PlaylistDetail,
    summary="Get the room's playlist",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No such room, or it has no playlist yet."},
    },
)
async def get_playlist(room_id: uuid.UUID, session: SessionDep) -> PlaylistDetail:
    await _require_room(session, room_id)
    playlist = await session.get(Playlist, room_id)
    if playlist is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="room has no playlist yet")
    return _detail(playlist, await _load_tracks(session, room_id))


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistDetail,
    summary="Import a Spotify playlist",
    description=(
        "Resolves the Spotify playlist server-side and copies its tracks into the "
        "room's playlist, creating the playlist if needed. Replaces the existing "
        "tracks unless `replace` is `false`. Tracks already present (by Spotify id) "
        "are skipped."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No such room, or Spotify has no such playlist."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Not a valid Spotify playlist reference."
        },
        status.HTTP_502_BAD_GATEWAY: {"description": "Spotify request failed."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Spotify is not configured on the server."
        },
    },
)
async def import_playlist(
    room_id: uuid.UUID,
    payload: PlaylistImportRequest,
    session: SessionDep,
    spotify: SpotifyDep,
) -> PlaylistDetail:
    await _require_room(session, room_id)
    try:
        found = await spotify.fetch_playlist_tracks(payload.playlist_url)
    except SpotifyError as exc:
        raise _spotify_error(exc) from exc

    playlist = await session.get(Playlist, room_id)
    if playlist is None:
        playlist = _new_playlist(room_id, payload.playlist_url)
        session.add(playlist)

    existing = await _load_tracks(session, room_id)
    if payload.replace:
        for track in existing:
            await session.delete(track)
        await session.flush()
        existing = []
        playlist.source_url = payload.playlist_url

    seen = {track.spotify_track_id for track in existing}
    position = max((track.position for track in existing), default=-1) + 1
    for track in found:
        if track.track_id in seen:
            continue
        seen.add(track.track_id)
        session.add(_track_row(room_id, position, track))
        position += 1

    await session.commit()
    return _detail(playlist, await _load_tracks(session, room_id))


@router.post(
    "/tracks",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistTrackDetail,
    summary="Add one track",
    description=(
        "Resolves a single Spotify track server-side and appends it to the room's "
        "playlist, creating the playlist if needed."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No such room, or Spotify has no such track."},
        status.HTTP_409_CONFLICT: {"description": "That track is already in the playlist."},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Not a valid Spotify track reference."
        },
        status.HTTP_502_BAD_GATEWAY: {"description": "Spotify request failed."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Spotify is not configured on the server."
        },
    },
)
async def add_track(
    room_id: uuid.UUID,
    payload: TrackAddRequest,
    session: SessionDep,
    spotify: SpotifyDep,
) -> PlaylistTrackDetail:
    await _require_room(session, room_id)
    try:
        found = await spotify.fetch_track(payload.track_url)
    except SpotifyError as exc:
        raise _spotify_error(exc) from exc

    if await session.get(Playlist, room_id) is None:
        session.add(_new_playlist(room_id, None))

    existing = await _load_tracks(session, room_id)
    if any(track.spotify_track_id == found.track_id for track in existing):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="track already in the playlist")

    position = max((track.position for track in existing), default=-1) + 1
    row = _track_row(room_id, position, found)
    session.add(row)
    await session.commit()
    return PlaylistTrackDetail.model_validate(row)
