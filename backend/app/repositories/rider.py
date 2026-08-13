from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.domain import Rider
from app.repositories.base import BaseRepository


class RiderRepository(BaseRepository[Rider]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Rider)

    def get(self, entity_id):  # type: ignore[override]
        return self.db.scalar(select(Rider).options(joinedload(Rider.user)).where(Rider.id == entity_id))

    def list(self) -> list[Rider]:  # type: ignore[override]
        query = select(Rider).options(joinedload(Rider.user)).order_by(Rider.id)
        return list(self.db.scalars(query).unique())
