"""drop legacy user email unique index

Revision ID: b4e2c8d9f1a0
Revises: e7b9c2d1a4f6
Create Date: 2026-10-18
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4e2c8d9f1a0"
down_revision: Union[str, Sequence[str], None] = "e7b9c2d1a4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Keep only the active-user email uniqueness rule.

    The initial migration does not create this index, but existing databases can
    contain it from an earlier schema.  Checking first also keeps fresh installs
    compatible with the recorded migration history.
    """
    indexes = sa.inspect(op.get_bind()).get_indexes("users")
    if any(index["name"] == "email" and index.get("unique") for index in indexes):
        op.drop_index("email", table_name="users")


def downgrade() -> None:
    """The recorded pre-migration schema has no standalone email index."""
