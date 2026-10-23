from typing import Annotated

from fastapi import APIRouter, Path, status

from app.philosophers.schemas import (
    PhilosopherDetailResponse,
    PhilosopherSummaryResponse,
)
from app.philosophers.service import PhilosopherServiceDep

router = APIRouter(prefix="/philosophers", tags=["철학자"])

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
    response_model=list[PhilosopherDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="철학자 전체 목록 조회",
    description="활성화된 모든 철학자의 전체 상세 정보를 조회합니다.",
)
def list_philosophers(
    service: PhilosopherServiceDep,
) -> list[PhilosopherDetailResponse]:
    return service.list_philosophers()


@router.get(
    "/summaries",
    response_model=list[PhilosopherSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="철학자 요약 목록 조회",
    description="활성화된 철학자의 요약 목록(id, 이름, 소개문구, 아이콘, 아바타 색상)을 조회합니다.",
)
def list_philosopher_summaries(
    service: PhilosopherServiceDep,
) -> list[PhilosopherSummaryResponse]:
    return service.list_philosopher_summaries()


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
