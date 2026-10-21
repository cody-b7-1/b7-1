from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.philosophers.schemas import (
    PhilosopherDetailResponse,
    PhilosopherListItem,
)
from app.philosophers.service import PhilosopherService

router = APIRouter(prefix="/philosophers", tags=["철학자"])

PhilosopherServiceDep = Annotated[PhilosopherService, Depends(PhilosopherService)]
PhilosopherIdPath = Annotated[
    int,
    Path(
        description="철학자 ID",
        examples=[1],
        gt=0,
    ),
]


@router.get(
    "",
    response_model=list[PhilosopherListItem],
    status_code=status.HTTP_200_OK,
    summary="철학자 목록 조회",
    description="활성화된 철학자 목록을 조회합니다.",
)
def list_philosophers(
    service: PhilosopherServiceDep,
) -> list[PhilosopherListItem]:
    return service.list_philosophers()


@router.get(
    "/{philosopher_id}",
    response_model=PhilosopherDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="철학자 상세 조회",
    description="특정 철학자의 상세 정보를 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "해당 철학자를 찾을 수 없거나 비활성화 상태입니다.",
        },
    },
)
def get_philosopher(
    philosopher_id: PhilosopherIdPath,
    service: PhilosopherServiceDep,
) -> PhilosopherDetailResponse:
    return service.get_philosopher(philosopher_id)
