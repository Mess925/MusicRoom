"""create playlists and playlist_tracks tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("edit_tier", sa.String(length=16), nullable=False),
        sa.Column("source_url", sa.String(length=400), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("room_id"),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            name="fk_playlists_room_id_rooms",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("visibility IN ('public', 'private')", name="ck_playlists_visibility"),
        sa.CheckConstraint(
            "edit_tier IN ('everyone', 'restricted')", name="ck_playlists_edit_tier"
        ),
    )
    op.create_table(
        "playlist_tracks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("spotify_uri", sa.String(length=64), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=400), nullable=False),
        sa.Column("artists", sa.JSON(), nullable=False),
        sa.Column("album", sa.String(length=400), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("artwork_url", sa.String(length=600), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.room_id"],
            name="fk_playlist_tracks_playlist_id_playlists",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("playlist_id", "position", name="uq_playlist_tracks_position"),
        sa.UniqueConstraint(
            "playlist_id", "spotify_track_id", name="uq_playlist_tracks_spotify_track_id"
        ),
    )
    op.create_index("ix_playlist_tracks_playlist_id", "playlist_tracks", ["playlist_id"])


def downgrade() -> None:
    op.drop_index("ix_playlist_tracks_playlist_id", table_name="playlist_tracks")
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
