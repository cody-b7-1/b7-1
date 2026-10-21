from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat
    from app.chats.models.message import Message


class Philosopher(CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "philosophers"

    philosopher_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    introduction: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ink_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    soft_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )

    current_chats: Mapped[list[Chat]] = relationship(
        back_populates="current_philosopher"
    )
    messages: Mapped[list[Message]] = relationship(back_populates="philosopher")
