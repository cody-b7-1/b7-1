from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum as SAEnum, String, TIMESTAMP, UUID as SAUUID, text
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

    user_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
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
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))
    email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    email_verification: Mapped[EmailVerification | None] = relationship(
        back_populates="user", uselist=False
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    chats: Mapped[list[Chat]] = relationship(back_populates="user")
