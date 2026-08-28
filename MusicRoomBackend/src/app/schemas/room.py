import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.room import RoomVisibility


class RoomCreate(BaseModel):
    """Body for creating a room. Visibility comes from the endpoint, not here."""

    name: str | None = Field(default=None, max_length=120, description="Optional display name.")


class RoomCreated(BaseModel):
    """Returned once, right after creation — the only time the access code is exposed."""

    id: uuid.UUID = Field(description="Pass this to join the room.")
    visibility: RoomVisibility
    access_code: str | None = Field(
        default=None,
        description="Present only for private rooms. Required, together with the id, to join.",
    )


class RoomJoinRequest(BaseModel):
    """Body for joining a room. Public rooms ignore it; private rooms require `access_code`."""

    access_code: str | None = Field(default=None)


class RoomDeleteRequest(BaseModel):
    """Body for deleting a room.

    ``confirmation_code`` must match the room's access code (private rooms) or
    its id as a string (public rooms). Knowing that value is what identifies the
    caller as the owner — there is no auth layer yet.
    """

    confirmation_code: str = Field(
        description="Access code for a private room, or the room id for a public one.",
    )


class RoomDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str | None
    visibility: RoomVisibility
