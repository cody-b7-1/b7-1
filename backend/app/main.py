from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel, Field

from app.auth.router import router as auth_router
from app.core.config import settings

class HealthResponse(BaseModel):
    """Response returned when the API process is available."""

    status: Literal["ok"] = Field(description="API availability status", examples=["ok"])


app = FastAPI(
    title="Philo API",
    version="0.1.0",
    description="Philo backend API specification generated from FastAPI routes.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(auth_router)


if settings.is_local_development:
    from app.dev.router import router as dev_router #dev 환경에서 test jwt 생성용 router 추가 

    app.include_router(dev_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The API could not process the health-check request."
        }
    },
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
