from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base every ORM model inherits from.

    No models are defined yet — import them here once they exist so Alembic
    autogenerate can see them on Base.metadata.
    """
