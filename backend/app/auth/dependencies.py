"""FastAPI dependencies for authenticated requests."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models.user import User
from app.auth.security import verify_access_token
from app.db.session import get_db

#요청의 Authorization 헤더에서 Bearer 인증 정보를 추출
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않거나 만료된 액세스 토큰입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the bearer token and return its non-deleted user."""
    if credentials is None:
        raise _unauthorized()

    #토큰 검증 
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError, TypeError):
        raise _unauthorized() from None

    #사용자 조회
    user = db.scalar(
        select(User).where(
            User.user_id == user_id,
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise _unauthorized()

    return user
