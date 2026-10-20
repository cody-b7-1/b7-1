from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models.user import Role, User
from app.auth.security import create_access_token, create_refresh_token

# Ensure relationship targets are registered before a User instance is mapped.
from app.db.session import get_db

DEV_USER_EMAIL = "dev@example.com"

router = APIRouter(prefix="/dev", tags=["개발"])


class DevAuthErrorResponse(BaseModel):
    detail: Annotated[
        str,
        Field(
            description="개발용 JWT를 발급하지 못한 이유입니다.",
            examples=["액세스 토큰을 발급하려면 JWT_SECRET_KEY 설정이 필요합니다."],
        ),
    ]


@router.post(
    "/auth",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="개발용 JWT 발급",
    description=(
        "로컬 개발용 사용자를 생성하거나 재사용하고, 로그인 API와 동일하게 HTTP 전용"
        "(HttpOnly) accessToken 및 refreshToken 쿠키를 설정합니다. 응답 본문은 반환하지 "
        "않습니다. 이 엔드포인트는 APP_ENV가 local일 때만 등록됩니다."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "개발용 JWT 발급에 성공했습니다. accessToken 및 refreshToken 쿠키를 설정합니다.",
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "accessToken 쿠키는 HTTP 전용(HttpOnly), 보안(Secure), SameSite=Lax, "
                        "Path=/api 속성을, refreshToken 쿠키는 같은 속성과 Path=/api/auth "
                        "속성을 가집니다. 각 쿠키는 별도의 Set-Cookie 헤더로 반환합니다."
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": DevAuthErrorResponse,
            "description": "개발용 사용자 또는 JWT를 생성하지 못했습니다.",
        },
    },
)
def issue_dev_access_token(response: Response, db: Session = Depends(get_db)) -> None:

    # scalar : SQLAlchemy Session 객체가 가진 메서드
    user = db.scalar(
        select(User).where(User.email == DEV_USER_EMAIL, User.deleted_at.is_(None))
    )
    # user 생성
    if user is None:
        user = User(
            user_id=uuid4(),
            email=DEV_USER_EMAIL,
            nickname="Development User",
            password_hash="!development-user-no-password!",
            role=Role.USER,
            email_verified_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(user)
    else:
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC).replace(tzinfo=None)

    db.commit()

    response.set_cookie(
        key="accessToken",
        value=create_access_token(user.user_id),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api",
    )
    response.set_cookie(
        key="refreshToken",
        value=create_refresh_token(user.user_id),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/auth",
    )
