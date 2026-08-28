import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.playlist import PlaylistEditTier, PlaylistVisibility


class PlaylistImportRequest(BaseModel):
    """Import every track of a Spotify playlist into the room's playlist."""

    playlist_url: str = Field(
        description=(
            "Spotify playlist link, URI, or bare id "
            "(https://open.spotify.com/playlist/..., spotify:playlist:..., or the id)."
        ),
    )
    replace: bool = Field(
        default=True,
        description="Replace the current tracks (default), or append to them.",
    )


class TrackAddRequest(BaseModel):
    """Add a single Spotify track to the end of the room's playlist."""

    track_url: str = Field(description="Spotify track link, URI, or bare id.")


class PlaylistTrackDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    spotify_uri: str
    spotify_track_id: str
    title: str
    artists: list[str]
    album: str | None
    duration_ms: int | None
    artwork_url: str | None


class PlaylistDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: uuid.UUID
    name: str | None
    visibility: PlaylistVisibility
    edit_tier: PlaylistEditTier
    source_url: str | None
    tracks: list[PlaylistTrackDetail]
