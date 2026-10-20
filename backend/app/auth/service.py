from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models.user import Role, User
from app.auth.schemas import SignUpRequest
from app.auth.security import hash_password


class EmailAlreadyRegisteredError(Exception):
    """Raised when an active account already uses the requested email address."""


def _is_active_email_duplicate(error: IntegrityError) -> bool:
    """Return whether MariaDB reported the active-user email constraint."""
    return "uq_users_email_active_marker" in str(error.orig)


def create_user(db: Session, request: SignUpRequest) -> User:
    """Create and persist a user with a normalized email and Argon2id password hash."""
    user = User(
        user_id=uuid4(),
        email=str(request.email).lower(),
        nickname=request.nickname,
        password_hash=hash_password(request.password),
        role=Role.USER,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_active_email_duplicate(error):
            raise EmailAlreadyRegisteredError("이미 등록된 이메일 주소입니다.") from error
        raise

    return user
