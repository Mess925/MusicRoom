"""ORM models.

Importing this package imports every model module, so ``Base.metadata`` is
fully populated for Alembic autogenerate and ``create_all``. Add new models
here as they land.
"""

from app.models.room import Room, RoomVisibility

__all__ = ["Room", "RoomVisibility"]
