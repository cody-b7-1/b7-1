"""add philosopher profile image url

Revision ID: c1d3e5f7a9b2
Revises: b4e2c8d9f1a0
Create Date: 2026-10-18
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d3e5f7a9b2"
down_revision: Union[str, Sequence[str], None] = "b4e2c8d9f1a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "philosophers",
        sa.Column("profile_image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("philosophers", "profile_image_url")
