from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import Role, User
from app.auth.schemas import LoginRequest, SignUpRequest
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.config import settings


class EmailAlreadyRegisteredError(Exception):
    """Raised when an active account already uses the requested email address."""


class EmailNotFoundError(Exception):
    """Raised when no account uses the supplied email address."""


class PasswordMismatchError(Exception):
    """Raised when the supplied password does not match the account."""

class InactiveAccountError(Exception): #휴면
    """Raised when the account has been deactivated."""


class EmailNotVerifiedError(Exception):
    """Raised when an otherwise usable account has not verified its email."""


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
            raise EmailAlreadyRegisteredError from error
        raise

    return user


def authenticate_user(db: Session, request: LoginRequest) -> User:
    """Authenticate an active, verified user from an email/password request."""
    email = str(request.email).lower()
    user = db.scalar(
        select(User).where(User.email == email, User.deleted_at.is_(None)) #삭제되지 않은 user 조회 
    )

    if user is None:
        raise EmailNotFoundError

    if not verify_password(request.password, user.password_hash):
        raise PasswordMismatchError

    if not user.is_active:
        raise InactiveAccountError

    if user.email_verified_at is None:
        raise EmailNotVerifiedError

    return user


def issue_refresh_token(db: Session, user: User) -> str:
    """Issue a refresh JWT with a jti and persist its hashed record."""
    token_id = uuid4()
    refresh_token = create_refresh_token(user.user_id, token_id=token_id)
    db.add(
        RefreshToken(
            token_id=token_id,
            user_id=user.user_id,
            token_hash=hash_password(refresh_token),
            expires_at=(
                datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
            ).replace(tzinfo=None),
        )
    )
    db.commit()
    return refresh_token


def login_user(db: Session, request: LoginRequest) -> tuple[str, str]:
    """Authenticate a user and issue persisted refresh and access tokens."""
    user = authenticate_user(db, request)
    refresh_token = issue_refresh_token(db, user)
    access_token = create_access_token(user.user_id)
    return access_token, refresh_token
