from sqlalchemy.orm import Session

from app.models.domain import TripStatusHistory
from app.repositories.base import BaseRepository


class TripStatusHistoryRepository(BaseRepository[TripStatusHistory]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TripStatusHistory)
