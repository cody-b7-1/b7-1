"""add active user email constraint

Revision ID: e7b9c2d1a4f6
Revises: 6a74c35a1593
Create Date: 2026-10-13
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7b9c2d1a4f6"
down_revision: Union[str, Sequence[str], None] = "6a74c35a1593"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "active_marker",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN deleted_at IS NULL THEN 1 ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_users_email_active_marker",
        "users",
        ["email", "active_marker"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_email_active_marker", "users", type_="unique")
    op.drop_column("users", "active_marker")
