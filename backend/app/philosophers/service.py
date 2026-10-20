from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.session import DBSession
from app.philosophers.models.philosopher import Philosopher
from app.philosophers.schemas import (
    PhilosopherDetailResponse,
    PhilosopherListItem,
)


class PhilosopherService:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def list_philosophers(self) -> list[PhilosopherListItem]:
        stmt = (
            select(Philosopher)
            .where(Philosopher.is_active.is_(True))
            .order_by(Philosopher.philosopher_id.asc())
        )
        philosophers = self.db.scalars(stmt).all()
        return [
            PhilosopherListItem.model_validate(philosopher)
            for philosopher in philosophers
        ]

    def get_philosopher(self, philosopher_id: int) -> PhilosopherDetailResponse:
        philosopher = self.db.get(Philosopher, philosopher_id)
        if philosopher is None or not philosopher.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 철학자를 찾을 수 없습니다.",
            )
        return PhilosopherDetailResponse.model_validate(philosopher)
