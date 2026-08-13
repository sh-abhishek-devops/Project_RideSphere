from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Payment)

    def get_by_trip_id(self, trip_id: UUID) -> Payment | None:
        return self.db.scalar(select(Payment).where(Payment.trip_id == trip_id))
