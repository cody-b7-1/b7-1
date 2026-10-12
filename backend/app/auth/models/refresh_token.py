from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, TIMESTAMP, UUID as SAUUID, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.auth.models.user import User


class RefreshToken(CreatedAtMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_id", "user_id"),)

    token_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
