from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Computed,
    Enum as SAEnum,
    Integer,
    String,
    TIMESTAMP,
    UUID as SAUUID,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin, SoftDeleteMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat
    from app.auth.models.email_verification import EmailVerification
    from app.auth.models.refresh_token import RefreshToken


class Role(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(CreatedAtMixin, UpdatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", "active_marker", name="uq_users_email_active_marker"),
    )

    user_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    active_marker: Mapped[int | None] = mapped_column(
        Integer,
        Computed(
            "CASE WHEN deleted_at IS NULL THEN 1 ELSE NULL END",
            persisted=True,
        ),
        nullable=True,
    )
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(
            Role,
            native_enum=False,
            length=20,
            values_callable=lambda role: [member.value for member in role],
            validate_strings=True,
        ),
        nullable=False,
        default=Role.USER,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    email_verifications: Mapped[list[EmailVerification]] = relationship(
        back_populates="user"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    chats: Mapped[list[Chat]] = relationship(back_populates="user")
