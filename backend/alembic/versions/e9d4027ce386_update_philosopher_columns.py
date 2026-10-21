"""update philosopher columns

Revision ID: e9d4027ce386
Revises: c1d3e5f7a9b2
Create Date: 2026-10-20 11:37:51.483432

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9d4027ce386"
down_revision: str | Sequence[str] | None = "c1d3e5f7a9b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("philosophers", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "philosophers",
        sa.Column("icon_image_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "philosophers", sa.Column("avatar_color", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "philosophers", sa.Column("ink_color", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "philosophers", sa.Column("soft_color", sa.String(length=20), nullable=True)
    )
    op.alter_column(
        "philosophers",
        "introduction",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "philosophers",
        "introduction",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("philosophers", "soft_color")
    op.drop_column("philosophers", "ink_color")
    op.drop_column("philosophers", "avatar_color")
    op.drop_column("philosophers", "icon_image_url")
    op.drop_column("philosophers", "description")
