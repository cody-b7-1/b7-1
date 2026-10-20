"""FastAPI dependencies for authenticated requests."""

from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models.user import User
from app.auth.security import verify_access_token
from app.db.session import get_db


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않거나 만료된 액세스 토큰입니다.",
    )


def get_current_user(
    access_token: str | None = Cookie(default=None, alias="accessToken"),
    db: Session = Depends(get_db),
) -> User:
    """Validate the access-token cookie and return its non-deleted user."""
    if access_token is None:
        raise _unauthorized()

    # 토큰 검증
    try:
        payload = verify_access_token(access_token)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError, TypeError):
        raise _unauthorized() from None

    # 사용자 조회
    user = db.scalar(
        select(User).where(
            User.user_id == user_id,
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise _unauthorized()

    return user
