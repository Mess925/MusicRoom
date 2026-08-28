"""The ``playlists`` and ``playlist_tracks`` tables.

Each room has at most one playlist — ``playlists.room_id`` is the primary key and
a ``rooms.id`` foreign key, so the playlist is deleted with its room. Tracks are
ordered by ``position`` and carry a snapshot of the Spotify metadata resolved
when they were added, so display and playback need no further Spotify calls.

``visibility`` / ``edit_tier`` mirror the tiers in ``REQUIREMENT.md`` §4.3. The
current routes only ever write the defaults; they exist for the collaborative
editor still to come.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlaylistVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class PlaylistEditTier(str, Enum):
    EVERYONE = "everyone"
    RESTRICTED = "restricted"


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        CheckConstraint("visibility IN ('public', 'private')", name="ck_playlists_visibility"),
        CheckConstraint("edit_tier IN ('everyone', 'restricted')", name="ck_playlists_edit_tier"),
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("rooms.id", ondelete="CASCADE", name="fk_playlists_room_id_rooms"),
        primary_key=True,
    )
    name: Mapped[str | None] = mapped_column(String(200), default=None)
    visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PlaylistVisibility.PUBLIC.value
    )
    edit_tier: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PlaylistEditTier.EVERYONE.value
    )
    # The Spotify playlist this was last imported from; ``None`` for a playlist
    # built up track by track.
    source_url: Mapped[str | None] = mapped_column(String(400), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlist_tracks_position"),
        UniqueConstraint(
            "playlist_id", "spotify_track_id", name="uq_playlist_tracks_spotify_track_id"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    playlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey(
            "playlists.room_id",
            ondelete="CASCADE",
            name="fk_playlist_tracks_playlist_id_playlists",
        ),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    spotify_uri: Mapped[str] = mapped_column(String(64), nullable=False)
    spotify_track_id: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    # Artist names in Spotify's order. JSON, not a delimited string — names can
    # contain any punctuation ("Tyler, the Creator").
    artists: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    album: Mapped[str | None] = mapped_column(String(400), default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    artwork_url: Mapped[str | None] = mapped_column(String(600), default=None)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
