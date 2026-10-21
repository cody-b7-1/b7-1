from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models.user import User
from app.auth.security import (
    verify_access_token,
    verify_refresh_token,
)
from app.db.session import get_db


def _access_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않거나 만료된 액세스 토큰입니다.",
    )


def _refresh_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않거나 만료된 리프레시 토큰입니다.",
    )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie(alias="accessToken")] = None,
) -> User:
    if access_token is None:
        raise _access_unauthorized()

    # 토큰 검증
    try:
        payload = verify_access_token(access_token)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError, TypeError):
        raise _access_unauthorized() from None

    # 사용자 조회
    user = db.scalar(
        select(User).where(
            User.user_id == user_id,
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise _access_unauthorized()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# logout 용
def get_optional_refresh_token(
    refresh_token: Annotated[str | None, Cookie(alias="refreshToken")] = None,
) -> str | None:
    if refresh_token is None:
        return None

    try:
        verify_refresh_token(refresh_token)
    except InvalidTokenError:  # 204로 반환
        return None

    return refresh_token


# refresh api용
def get_refresh_token(
    refresh_token: Annotated[
        str | None,
        Depends(get_optional_refresh_token),
    ],
) -> str:
    if refresh_token is None:  # jti 등의 누락 시 401
        raise _refresh_unauthorized()

    return refresh_token
