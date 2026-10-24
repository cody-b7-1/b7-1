import logging
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models.email_verification import EmailVerification
from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import Role, User
from app.auth.schemas import LoginRequest, SignUpRequest
from app.auth.security import (
    RefreshTokenPayload,
    create_access_token,
    create_refresh_token,
    hash_email_verification_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# 비즈니스 오류
# 회원가입용 - 이메일에 대한 사용자 이미 있는 경우 (삭제 x)
class EmailAlreadyRegisteredError(Exception):
    pass


# 비즈니스 오류
# 로그인용 - 요청한 이메일에 대한 사용자 x
class EmailNotFoundError(Exception):
    pass


# 로그인용 - 비밀번호 틀린 경우
class PasswordMismatchError(Exception):
    pass


# 로그인용 - 이메일 인증 x 경우
class EmailNotVerifiedError(Exception):
    pass


class InvalidEmailVerificationTokenError(Exception):
    """Raised when an email verification token is expired, used, or invalid."""


class InvalidRefreshTokenError(Exception):
    pass


# 실제 원인 (사용 중인 계정에 대한 중복 문제)
def _is_active_email_duplicate(error: IntegrityError) -> bool:
    return "uq_users_email_active_marker" in str(error.orig)


def create_user(db: Session, request: SignUpRequest) -> User:
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
            raise EmailAlreadyRegisteredError from error  # 비즈니스 오류
        raise

    logger.info("회원가입에 성공했습니다.")
    return user


def create_email_verification(db: Session, email: str) -> tuple[str, str] | None:

    # 사용자 조회 + 잠금
    user = db.scalar(
        select(User)
        .where(
            User.email == email.lower(),
            User.deleted_at.is_(None),
        )
        .with_for_update()
    )

    # 사용자가 없거나 이미 인증된 경우
    if user is None or user.email_verified_at is not None:
        db.rollback()
        return None

    # 새로운 토큰 생성
    token = token_urlsafe(32)

    expires_at = (
        datetime.now(UTC) + timedelta(hours=settings.email_verification_expire_hours)
    ).replace(tzinfo=None)

    # email verification 생성
    verification = EmailVerification(
        verification_id=uuid4(),
        user_id=user.user_id,
        token_hash=hash_email_verification_token(token),
        expires_at=expires_at,
    )

    db.add(verification)

    user_email = user.email
    db.commit()

    return user_email, token


def verify_email_verification_token(db: Session, token: str) -> None:
    try:
        now = datetime.now(UTC).replace(tzinfo=None)
        token_hash = hash_email_verification_token(token)

        # 1. 잠금 없이 해당 토큰 식별, 사용자 찾기
        matched = db.scalar(
            select(EmailVerification).where(
                EmailVerification.token_hash == token_hash,
                EmailVerification.expires_at > now,
            )
        )

        if matched is None:
            raise InvalidEmailVerificationTokenError

        # 2. 사용자 행 잠금
        user = db.scalar(
            select(User)
            .where(User.user_id == matched.user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if (
            user is None
            or user.deleted_at is not None
            or user.email_verified_at is not None
        ):
            raise InvalidEmailVerificationTokenError

        # 3. 잠금 획득 후 토큰 재확인
        now = datetime.now(UTC).replace(tzinfo=None)

        verification = db.scalar(
            select(EmailVerification)
            .where(
                EmailVerification.verification_id == matched.verification_id,
                EmailVerification.token_hash == token_hash,
                EmailVerification.expires_at > now,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if verification is None:
            raise InvalidEmailVerificationTokenError

        # 4. 인증 완료
        user.email_verified_at = now

        # 5. 관련된 해당 사용자의 모든 인증 토큰 삭제
        db.execute(
            delete(EmailVerification).where(EmailVerification.user_id == user.user_id)
        )

        db.commit()

    except Exception:
        db.rollback()
        raise


def authenticate_user(db: Session, request: LoginRequest) -> User:
    email = str(request.email).lower()
    user = db.scalar(
        select(User).where(
            User.email == email, User.deleted_at.is_(None)
        )  # 삭제되지 않은 user 조회
    )

    if user is None:
        logger.warning("로그인 인증에 실패했습니다.")
        raise EmailNotFoundError

    if not verify_password(request.password, user.password_hash):
        logger.warning("로그인 인증에 실패했습니다.")
        raise PasswordMismatchError

    if user.email_verified_at is None:
        logger.debug("이메일 인증이 완료되지 않아 로그인에 실패했습니다.")
        raise EmailNotVerifiedError

    return user


def issue_refresh_token(db: Session, user: User) -> str:
    token_id = uuid4()
    refresh_token = create_refresh_token(user.user_id, token_id=token_id)

    # db 저장 시 refresh token hashing
    db.add(
        RefreshToken(
            token_id=token_id,
            user_id=user.user_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=(
                datetime.now(UTC)
                + timedelta(days=settings.jwt_refresh_token_expire_days)
            ).replace(tzinfo=None),
        )
    )
    db.commit()
    return refresh_token


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    # Refresh Token 해싱
    token_hash = hash_refresh_token(refresh_token)

    # DB에서 해당 토큰 조회
    stored_token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )

    # 토큰이 없거나 이미 폐기된 경우
    if stored_token is None or stored_token.is_revoked:
        return

    # 해당 Refresh Token만 폐기
    stored_token.is_revoked = True
    db.commit()


def login_user(db: Session, request: LoginRequest) -> tuple[str, str]:
    user = authenticate_user(db, request)

    # refresh token, access token 생성
    access_token = create_access_token(user.user_id)
    refresh_token = issue_refresh_token(db, user)

    logger.info("로그인에 성공했습니다.")
    return access_token, refresh_token


def rotate_refresh_token(
    db: Session,
    payload: RefreshTokenPayload,
    refresh_token: str,
) -> tuple[str, str]:
    user_id = UUID(payload["sub"])

    # update

    try:
        # refresh token db에서 삭제(폐기)
        result = db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == hash_refresh_token(refresh_token),
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        if result.rowcount != 1:  # 실제 반영된 행의 수가 1개여야함
            raise InvalidRefreshTokenError

        # access, refresh jwt 생성
        new_token_id = uuid4()
        new_refresh_token = create_refresh_token(user_id, token_id=new_token_id)
        new_access_token = create_access_token(
            user_id
        )  # commit 밖에 놓을 시 생성 실패 후 refresh token만 저장, 생성될 수 있음

        # refresh token db에 추가
        db.add(
            RefreshToken(
                token_id=new_token_id,
                user_id=user_id,
                token_hash=hash_refresh_token(new_refresh_token),
                expires_at=(
                    datetime.now(UTC)
                    + timedelta(days=settings.jwt_refresh_token_expire_days)
                ).replace(tzinfo=None),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return new_access_token, new_refresh_token
