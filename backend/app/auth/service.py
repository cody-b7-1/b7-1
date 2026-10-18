from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models.user import Role, User
from app.auth.schemas import LoginRequest, SignUpRequest
from app.auth.security import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    """Raised when an active account already uses the requested email address."""


class InvalidCredentialsError(Exception):
    """Raised when the supplied email and password do not identify a user."""


class LoginUnavailableError(Exception):
    """Raised when an account exists but cannot be used to log in."""


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
        is_active=True,
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


def authenticate_user(db: Session, request: LoginRequest) -> User:
    """Authenticate an active, verified user from an email/password request."""
    email = str(request.email).lower()
    user = db.scalar(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )

    if user is None:
        deleted_user = db.scalar(
            select(User).where(User.email == email, User.deleted_at.is_not(None))
        )
        if deleted_user is not None:
            raise LoginUnavailableError("로그인할 수 없는 계정입니다.")
        raise InvalidCredentialsError("이메일 주소 또는 비밀번호가 일치하지 않습니다.")

    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError("이메일 주소 또는 비밀번호가 일치하지 않습니다.")

    if not user.is_active or user.email_verified_at is None:
        raise LoginUnavailableError("로그인할 수 없는 계정입니다.")

    return user
