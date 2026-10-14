"""Shared primitives for issuing authentication tokens."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import settings


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:

    if not settings.jwt_secret_key: #signature 생성 키 
        raise RuntimeError("JWT_SECRET_KEY must be set before issuing access tokens")

    now = datetime.now(UTC)
    lifetime = expires_delta or timedelta(days=settings.jwt_access_token_expire_days) #없으면 설정값으로 
    payload: dict[str, str | int] = {
        "sub": str(user_id), #subject(토큰 주체)
        "iat": int(now.timestamp()), #발급 시각 
        "exp": int((now + lifetime).timestamp()), #만료 시각
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
