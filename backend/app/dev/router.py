from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
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

    user_id: str = Field(serialization_alias="userId")
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(serialization_alias="tokenType")

#test용 jwt 토큰 생성
@router.post("/test-auth", response_model=TestAuthResponse)
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
