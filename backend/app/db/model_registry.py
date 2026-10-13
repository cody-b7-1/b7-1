"""Register all SQLAlchemy models on :class:`app.db.base.Base` metadata.

Alembic imports this module before inspecting ``Base.metadata`` for
autogeneration.  Domain model definitions remain in their own packages.
"""

from app.auth.models.email_verification import EmailVerification
from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.philosophers.models.philosopher import Philosopher

__all__ = [
    "Chat",
    "EmailVerification",
    "Message",
    "Philosopher",
    "RefreshToken",
    "User",
]
