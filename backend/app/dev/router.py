from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

# Ensure relationship targets are registered before a User instance is mapped.
from app.db import model_registry as _model_registry
from app.auth.models.user import Role, User
from app.auth.security import create_access_token
from app.db.session import get_db


DEV_USER_EMAIL = "dev@example.com"

router = APIRouter(prefix="/dev", tags=["개발"])


class DevAuthResponse(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    user_id: Annotated[
        str,
        Field(
            serialization_alias="userId",
            description="개발용 사용자의 UUID입니다.",
        ),
    ]
    access_token: Annotated[
        str,
        Field(
            serialization_alias="accessToken",
            description="인증이 필요한 API 호출용 JWT 액세스 토큰입니다.",
        ),
    ]
    token_type: Annotated[
        str,
        Field(
            serialization_alias="tokenType",
            description="액세스 토큰의 인증 방식입니다.",
            examples=["bearer"],
        ),
    ]


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
    response_model=DevAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="개발용 JWT 발급",
    description=(
        "로컬 개발용 사용자를 생성하거나 재사용하고 액세스 토큰을 반환합니다. 이 "
        "엔드포인트는 APP_ENV가 local일 때만 등록됩니다."
    ),
    responses={
        status.HTTP_200_OK: {"description": "개발용 JWT 발급에 성공했습니다."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": DevAuthErrorResponse,
            "description": "개발용 사용자 또는 JWT를 생성하지 못했습니다.",
        }
    },
)
def issue_dev_access_token(db: Session = Depends(get_db)) -> DevAuthResponse:
   
    #scalar : SQLAlchemy Session 객체가 가진 메서드 
    user = db.scalar(
        select(User).where(User.email == DEV_USER_EMAIL, User.deleted_at.is_(None))
    )
    #user 생성
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

    return DevAuthResponse(
        user_id=str(user.user_id),
        access_token=create_access_token(user.user_id),
        token_type="bearer",
    )
