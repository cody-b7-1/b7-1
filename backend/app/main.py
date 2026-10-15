from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel, Field

from app.auth.router import router as auth_router
from app.core.config import settings

class HealthResponse(BaseModel):
    """Response returned when the API process is available."""

    status: Literal["ok"] = Field(description="API 사용 가능 상태입니다.", examples=["ok"])


app = FastAPI(
    title="Philo API",
    version="0.1.0",
    description="FastAPI 라우트에서 생성한 Philo 백엔드 API 명세입니다.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(auth_router)


if settings.is_local:
    from app.dev.router import router as dev_router #dev 환경에서 test jwt 생성용 router 추가 

    app.include_router(dev_router)


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
