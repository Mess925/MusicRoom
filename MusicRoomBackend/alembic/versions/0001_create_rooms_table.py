"""create rooms table

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("access_code", sa.String(length=12), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("visibility IN ('public', 'private')", name="ck_rooms_visibility"),
    )
    op.create_index("ix_rooms_access_code", "rooms", ["access_code"])


def downgrade() -> None:
    op.drop_index("ix_rooms_access_code", table_name="rooms")
    op.drop_table("rooms")
