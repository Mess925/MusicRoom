"""The ``rooms`` table.

A room is a joinable space. ``public`` rooms need only their id to join;
``private`` rooms also require the ``access_code`` generated when the room is
created.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoomVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint("visibility IN ('public', 'private')", name="ck_rooms_visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(String(120), default=None)
    # Stored as its string value ("public" / "private"). The enum is enforced at
    # the API boundary by the Pydantic schemas.
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    # Set only for private rooms; ``None`` for public ones.
    access_code: Mapped[str | None] = mapped_column(String(12), default=None, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
