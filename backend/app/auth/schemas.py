from datetime import timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.config import settings


ACCESS_TOKEN_EXPIRES_IN_SECONDS = int(
    timedelta(days=settings.jwt_access_token_expire_days).total_seconds()
)


class SignUpRequest(BaseModel):
    """회원가입 요청입니다."""

    email: Annotated[
        EmailStr,
        Field(
            max_length=254,
            json_schema_extra={"format": "email"},
            description="회원 이메일 주소입니다.",
            examples=["user@example.com"],
        ),
    ]
    nickname: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="회원 닉네임입니다.",
            examples=["철학탐험가"],
        ),
    ]
    password: str = Field(
        min_length=8,
        max_length=128,
        description="HTTPS로 전송하는 비밀번호입니다.",
        examples=["password123!"],
    )


class LoginRequest(BaseModel):
    """이메일과 비밀번호로 로그인하는 요청입니다."""

    email: Annotated[
        EmailStr,
        Field(
            max_length=254,
            description="회원 이메일 주소입니다.",
            examples=["user@example.com"],
        ),
    ]
    password: str = Field(
        max_length=128,
        description="HTTPS로 전송하는 비밀번호입니다.",
        examples=["password123!"],
    )


class EmailSendRequest(BaseModel):
    """이메일 인증 링크 발송 요청입니다."""

    email: Annotated[
        EmailStr,
        Field(
            max_length=254,
            description="회원 이메일 주소입니다.",
            examples=["user@example.com"],
        ),
    ]


class EmailVerifyRequest(BaseModel):
    """이메일 인증 링크 토큰 검증 요청입니다."""

    token: str = Field(
        description="이메일 인증 링크에서 받은 토큰입니다.",
        examples=["opaque-one-time-token"],
    )


class LoginResponse(BaseModel):
    """로그인 또는 액세스 토큰 갱신 성공 응답입니다."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(
        serialization_alias="accessToken",
        description="JWT 액세스 토큰입니다.",
        examples=["eyJhbGciOi..."],
    )
    token_type: Literal["Bearer"] = Field(
        serialization_alias="tokenType",
        description="액세스 토큰의 인증 방식입니다.",
        examples=["Bearer"],
    )
    expires_in: int = Field(
        serialization_alias="expiresIn",
        description="액세스 토큰의 유효 기간(초)입니다.",
        examples=[ACCESS_TOKEN_EXPIRES_IN_SECONDS],
    )
