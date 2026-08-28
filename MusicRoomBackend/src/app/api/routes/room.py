"""Room creation and joining.

* ``POST /rooms/public``  — create a public room; returns its id.
* ``POST /rooms/private`` — create a private room; returns its id **and** a
  freshly generated access code.
* ``POST /rooms/{room_id}/join`` — join a room. Public rooms need only the id;
  private rooms also require the matching access code.
"""

import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tokens import generate_access_code
from app.db.session import get_session
from app.models.room import Room, RoomVisibility
from app.schemas.room import RoomCreate, RoomCreated, RoomDetail, RoomJoinRequest

router = APIRouter(prefix="/rooms", tags=["rooms"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _persist(session: AsyncSession, room: Room) -> Room:
    session.add(room)
    await session.commit()
    return room


@router.post(
    "/public",
    status_code=status.HTTP_201_CREATED,
    response_model=RoomCreated,
    summary="Create a public room",
    description="Anyone can join a public room with just the returned `id`.",
)
async def create_public_room(payload: RoomCreate, session: SessionDep) -> RoomCreated:
    room = await _persist(
        session,
        Room(id=uuid.uuid4(), name=payload.name, visibility=RoomVisibility.PUBLIC.value),
    )
    return RoomCreated(id=room.id, visibility=room.visibility, access_code=None)


@router.post(
    "/private",
    status_code=status.HTTP_201_CREATED,
    response_model=RoomCreated,
    summary="Create a private room",
    description=(
        "The access code is generated here and returned **once**. Joining a "
        "private room needs both the `id` and this `access_code`."
    ),
)
async def create_private_room(payload: RoomCreate, session: SessionDep) -> RoomCreated:
    room = await _persist(
        session,
        Room(
            id=uuid.uuid4(),
            name=payload.name,
            visibility=RoomVisibility.PRIVATE.value,
            access_code=generate_access_code(),
        ),
    )
    return RoomCreated(id=room.id, visibility=room.visibility, access_code=room.access_code)


@router.post(
    "/{room_id}/join",
    response_model=RoomDetail,
    summary="Join a room",
    description=(
        "Public rooms need only the `room_id`. Private rooms also require a "
        "matching `access_code` in the body — a wrong or missing code is a 403."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "Private room, wrong or missing access code."},
        status.HTTP_404_NOT_FOUND: {"description": "No room with that id."},
    },
)
async def join_room(
    room_id: uuid.UUID,
    session: SessionDep,
    payload: RoomJoinRequest | None = None,
) -> Room:
    room = await session.get(Room, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="room not found")

    if room.visibility == RoomVisibility.PRIVATE:
        supplied = (payload.access_code if payload else None) or ""
        if not secrets.compare_digest(supplied, room.access_code or ""):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="invalid or missing access code")

    return room
