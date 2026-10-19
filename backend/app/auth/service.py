from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models.email_verification import EmailVerification
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

#비즈니스 오류
#회원가입용 - 이메일에 대한 사용자 이미 있는 경우 (삭제 x)
class EmailAlreadyRegisteredError(Exception):
    """Raised when an active account already uses the requested email address."""

#비즈니스 오류 
#로그인용 - 요청한 이메일에 대한 사용자 x 
class EmailNotFoundError(Exception):
    """Raised when no account uses the supplied email address."""

#로그인용 - 비밀번호 틀린 경우 
class PasswordMismatchError(Exception):
    """Raised when the supplied password does not match the account."""

#로그인용 - 이메일 인증 x 경우
class EmailNotVerifiedError(Exception):
    """Raised when an otherwise usable account has not verified its email."""


class InvalidEmailVerificationTokenError(Exception):
    """Raised when an email verification token is expired, used, or invalid."""

#실제 원인 (사용 중인 계정에 대한 중복 문제)
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
            raise EmailAlreadyRegisteredError from error #비즈니스 오류
        raise

    return user


def create_email_verification(db: Session, user: User) -> str:
    """Create or replace a user's one-time email verification token."""
    token = token_urlsafe(32)
    # Locking the user row serializes resend requests for one account. This prevents
    # two concurrent requests from leaving different tokens valid at the same time.
    db.scalar(select(User).where(User.user_id == user.user_id).with_for_update())
    verification = db.scalar(
        select(EmailVerification)
        .where(EmailVerification.user_id == user.user_id)
        .with_for_update()
    )
    expires_at = (
        datetime.now(UTC) + timedelta(hours=settings.email_verification_expire_hours)
    ).replace(tzinfo=None)

    if verification is None:
        verification = EmailVerification(
            verification_id=uuid4(),
            user_id=user.user_id,
            token_hash=hash_password(token),
            expires_at=expires_at,
        )
        db.add(verification)
    else:
        verification.token_hash = hash_password(token)
        verification.expires_at = expires_at

    db.commit()
    return token


def verify_email_verification_token(db: Session, token: str) -> None:
    """Consume a valid verification token and mark its user as verified."""
    now = datetime.now(UTC).replace(tzinfo=None)

    verifications = db.scalars(
        select(EmailVerification)
        .where(EmailVerification.expires_at > now)
        .with_for_update()
    ).all()

    for verification in verifications:
        if verification.expires_at <= now:
            continue
        if not verify_password(token, verification.token_hash):
            continue

        user = verification.user
        
        if user.deleted_at is not None or user.email_verified_at is not None:
            raise InvalidEmailVerificationTokenError

        user.email_verified_at = now
        db.delete(verification)
        db.commit()
        return

    raise InvalidEmailVerificationTokenError


def authenticate_user(db: Session, request: LoginRequest) -> User:
    """Authenticate a non-deleted, verified user from an email/password request."""
    email = str(request.email).lower()
    user = db.scalar(
        select(User).where(User.email == email, User.deleted_at.is_(None)) #삭제되지 않은 user 조회 
    )

    if user is None:
        raise EmailNotFoundError

    if not verify_password(request.password, user.password_hash):
        raise PasswordMismatchError

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

    #refresh token, access token 생성
    refresh_token = issue_refresh_token(db, user) #db commit 하기 때문에 service에서 security method 호출해 사용
    access_token = create_access_token(user.user_id)
    return access_token, refresh_token
