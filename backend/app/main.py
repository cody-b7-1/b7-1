from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel, Field

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

class HealthResponse(BaseModel):
    """API 서버 상태 응답입니다."""

    status: Literal["ok"] = Field(description="API 사용 가능 상태입니다.", examples=["ok"])


app = FastAPI(
    title="Philo API",
    version="0.1.0",
    description="FastAPI 라우트에서 생성한 Philo 백엔드 API 명세입니다.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

register_exception_handlers(app)
app.include_router(auth_router, prefix="/api")


if settings.is_local:
    from app.dev.router import router as dev_router  # 개발 환경용 JWT 발급 라우터

    app.include_router(dev_router, prefix="/api")


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="상태 확인",
    responses={
        status.HTTP_200_OK: {"description": "API 상태가 정상입니다."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "API가 상태 확인 요청을 처리하지 못했습니다."
        }
    },
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
