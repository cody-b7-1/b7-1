from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from app.db.session import DBSession
from app.philosophers.exceptions import PhilosopherNotFoundError
from app.philosophers.models.philosopher import Philosopher
from app.philosophers.schemas import (
    PhilosopherDetailResponse,
    PhilosopherSummaryResponse,
)


class PhilosopherService:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def _get_active_philosophers(self) -> Sequence[Philosopher]:
        stmt = (
            select(Philosopher)
            .where(Philosopher.is_active.is_(True))
            .order_by(Philosopher.philosopher_id.asc())
        )
        return self.db.scalars(stmt).all()

    def list_philosophers(self) -> list[PhilosopherDetailResponse]:
        return [
            PhilosopherDetailResponse.model_validate(philosopher)
            for philosopher in self._get_active_philosophers()
        ]

    def list_philosopher_summaries(self) -> list[PhilosopherSummaryResponse]:
        return [
            PhilosopherSummaryResponse.model_validate(philosopher)
            for philosopher in self._get_active_philosophers()
        ]

    def get_philosopher(self, philosopher_id: int) -> PhilosopherDetailResponse:
        philosopher = self.db.get(Philosopher, philosopher_id)
        if philosopher is None or not philosopher.is_active:
            raise PhilosopherNotFoundError()
        return PhilosopherDetailResponse.model_validate(philosopher)


def get_philosopher_service(db: DBSession) -> PhilosopherService:
    return PhilosopherService(db=db)


PhilosopherServiceDep = Annotated[PhilosopherService, Depends(get_philosopher_service)]
