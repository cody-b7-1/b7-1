from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

EmailAddress = Annotated[
    EmailStr,
    Field(
        max_length=254,
        json_schema_extra={"format": "email"},
        description="회원 이메일 주소입니다.",
        examples=["user@example.com"],
    ),
]


class SignUpRequest(BaseModel):
    """회원가입 요청입니다."""

    email: EmailAddress
    nickname: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="회원 닉네임입니다.",
            examples=["철학탐험가"],
        ),
    ]
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=128,
            description="HTTPS로 전송하는 비밀번호입니다.",
            examples=["password123!"],
        ),
    ]


class LoginRequest(BaseModel):
    """이메일과 비밀번호로 로그인하는 요청입니다."""

    email: EmailAddress
    password: Annotated[
        str,
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
            min_length=8,
            max_length=128,
            description="HTTPS로 전송하는 비밀번호입니다.",
            examples=["password123!"],
        ),
    ]


class EmailSendRequest(BaseModel):
    """이메일 인증 링크 발송 요청입니다."""

    email: EmailAddress


class EmailVerifyRequest(BaseModel):
    """이메일 인증 링크 토큰 검증 요청입니다."""

    token: Annotated[
        str,
        Field(
            description="이메일 인증 링크에서 받은 토큰입니다.",
            examples=["opaque-one-time-token"],
        ),
    ]

