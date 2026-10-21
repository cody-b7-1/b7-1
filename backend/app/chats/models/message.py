from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.enums import SenderRole
from app.db.base import Base
from app.db.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat
    from app.philosophers.models.philosopher import Philosopher


class Message(CreatedAtMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_philosopher_id", "philosopher_id"),)

    message_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    chat_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), ForeignKey("chats.chat_id"), nullable=False
    )
    philosopher_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("philosophers.philosopher_id"), nullable=True
    )
    sender_role: Mapped[SenderRole] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_success: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, server_default=text("NULL")
    )

    chat: Mapped[Chat] = relationship(back_populates="messages")
    philosopher: Mapped[Philosopher | None] = relationship(back_populates="messages")
