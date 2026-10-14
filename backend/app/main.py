from fastapi import FastAPI

from app.core.config import settings

app = FastAPI()


if settings.is_local_development:
    from app.dev.router import router as dev_router #dev 환경에서 test jwt 생성용 router 추가 

    app.include_router(dev_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
