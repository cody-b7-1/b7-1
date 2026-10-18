"""Shared primitives for issuing authentication tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
TOKEN_TYPE_CLAIM = "type"
TokenType = Literal["access", "refresh"]
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Argon2id로 비밀번호를 해싱합니다."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """평문 비밀번호가 저장된 Argon2id 해시와 일치하는지 검증합니다."""
    return password_hasher.verify(password, password_hash)


def create_token(
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    token_id: UUID | None = None,
) -> str:
    """지정한 유형과 유효 기간으로 JWT를 생성합니다."""
    now = datetime.now(UTC)
    payload: dict[str, str | int] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        TOKEN_TYPE_CLAIM: token_type,
    }
    if token_id is not None:
        payload["jti"] = str(token_id)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """액세스 토큰을 생성합니다."""
    return create_token(
        user_id,
        ACCESS_TOKEN_TYPE,
        expires_delta or timedelta(days=settings.jwt_access_token_expire_days),
    )


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
    *,
    token_id: UUID | None = None,
) -> str:
    """리프레시 토큰을 생성합니다."""
    return create_token(
        user_id,
        REFRESH_TOKEN_TYPE,
        expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days),
        token_id or uuid4(),
    )


def verify_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """JWT의 서명, 만료 시간, 토큰 유형을 검증합니다."""
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    try:
        token_type = payload[TOKEN_TYPE_CLAIM]
    except KeyError as error:
        raise InvalidTokenError("토큰 유형 정보가 없습니다.") from error

    if token_type != expected_type:
        raise InvalidTokenError("토큰 유형이 올바르지 않습니다.")

    return payload


def verify_access_token(token: str) -> dict[str, Any]:
    """액세스 토큰을 검증합니다."""
    return verify_token(token, ACCESS_TOKEN_TYPE)


def verify_refresh_token(token: str) -> dict[str, Any]:
    """리프레시 토큰을 검증합니다."""
    return verify_token(token, REFRESH_TOKEN_TYPE)
