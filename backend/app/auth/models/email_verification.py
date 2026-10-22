from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, TIMESTAMP, UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.auth.models.user import User


class EmailVerification(CreatedAtMixin, Base):
    __tablename__ = "email_verifications"

    verification_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    user: Mapped[User] = relationship(back_populates="email_verifications")
