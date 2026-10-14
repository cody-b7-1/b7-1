from datetime import UTC, datetime
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


TEST_USER_EMAIL = "dev-test@philo.local"

router = APIRouter(prefix="/dev", tags=["development"])


class TestAuthResponse(BaseModel):
    """JWT issued by the local-development test authentication endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(
        serialization_alias="userId",
        description="Development test user's UUID.",
    )
    access_token: str = Field(
        serialization_alias="accessToken",
        description="JWT access token for calling authenticated APIs.",
    )
    token_type: str = Field(
        serialization_alias="tokenType",
        description="Authentication scheme for the access token.",
        examples=["bearer"],
    )


class TestAuthErrorResponse(BaseModel):
    """Error body documented for failures while issuing a test JWT."""

    detail: str = Field(
        description="Reason the development test JWT could not be issued.",
        examples=["JWT_SECRET_KEY must be set before issuing access tokens"],
    )


@router.post(
    "/test-auth",
    response_model=TestAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue a development test JWT",
    description=(
        "Creates or reuses the local development test user and returns an access token. "
        "This endpoint is registered only when APP_ENV is development."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": TestAuthErrorResponse,
            "description": "The test user or JWT could not be created.",
        }
    },
)
def issue_test_access_token(db: Session = Depends(get_db)) -> TestAuthResponse:
   
    #scalar : SQLAlchemy Session 객체가 가진 메서드 
    user = db.scalar(
        select(User).where(User.email == TEST_USER_EMAIL, User.deleted_at.is_(None))
    )
    #user 생성
    if user is None:
        user = User(
            user_id=uuid4(),
            email=TEST_USER_EMAIL,
            nickname="Development Test User",
            password_hash="!development-test-user-no-password!",
            role=Role.USER,
            is_active=True,
            email_verified_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(user)
    else:
        # 이미 사용자가 있는 경우 사용(활성화) 
        user.is_active = True
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC).replace(tzinfo=None)

    db.commit()

    return TestAuthResponse(
        user_id=str(user.user_id),
        access_token=create_access_token(user.user_id),
        token_type="bearer",
    )
