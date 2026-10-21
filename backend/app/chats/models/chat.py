from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as SAUUID
from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin, SoftDeleteMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from app.auth.models.user import User
    from app.chats.models.message import Message
    from app.philosophers.models.philosopher import Philosopher


class Chat(CreatedAtMixin, UpdatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "chats"
    __table_args__ = (
        Index("ix_chats_user_id", "user_id"),
        Index("ix_chats_current_philosopher_id", "current_philosopher_id"),
    )

    chat_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    current_philosopher_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("philosophers.philosopher_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(back_populates="chats")
    current_philosopher: Mapped[Philosopher] = relationship(
        back_populates="current_chats"
    )
    messages: Mapped[list[Message]] = relationship(back_populates="chat")
