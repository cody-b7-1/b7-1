"""이메일 인증 관계를 일대다로 변경

리비전 ID: f2a6c8e1d4b7
이전 리비전: e9d4027ce386
생성일: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic 리비전 식별자
revision: str = "f2a6c8e1d4b7"
down_revision: str | Sequence[str] | None = "e9d4027ce386"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    table = "email_verifications"
    index_name = "ix_email_verifications_user_id"
    temp_name = "ix_email_verifications_user_id_tmp"

    bind = op.get_bind()

    def get_indexes():
        return {idx["name"]: idx for idx in sa.inspect(bind).get_indexes(table)}

    indexes = get_indexes()

    # 기존 인덱스가 UNIQUE라면 FK 유지를 위한 임시 인덱스 생성
    if index_name in indexes and indexes[index_name]["unique"]:
        if temp_name not in indexes:
            op.create_index(temp_name, table, ["user_id"], unique=False)

    # 인덱스가 아예 없는 경우 일반 인덱스 생성
    elif index_name not in indexes:
        op.create_index(index_name, table, ["user_id"], unique=False)

    # user_id 단독 UNIQUE 제약 제거
    constraints = sa.inspect(bind).get_unique_constraints(table)

    for constraint in constraints:
        if constraint["column_names"] == ["user_id"]:
            op.drop_constraint(
                constraint["name"],
                table,
                type_="unique",
            )

    # 기존 UNIQUE 인덱스가 제거됐다면 일반 인덱스로 재생성
    if index_name not in get_indexes():
        op.create_index(index_name, table, ["user_id"], unique=False)

    # 임시 인덱스 제거
    if temp_name in get_indexes():
        op.drop_index(temp_name, table_name=table)


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_email_verifications_user_id",
        "email_verifications",
        ["user_id"],
    )
    op.drop_index(
        "ix_email_verifications_user_id",
        table_name="email_verifications",
    )
