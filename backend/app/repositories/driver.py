from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.domain import Driver
from app.repositories.base import BaseRepository


class DriverRepository(BaseRepository[Driver]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Driver)

    def get(self, entity_id):  # type: ignore[override]
        query = select(Driver).options(joinedload(Driver.user)).where(Driver.id == entity_id)
        return self.db.scalar(query)

    def list(self) -> list[Driver]:  # type: ignore[override]
        query = select(Driver).options(joinedload(Driver.user)).order_by(Driver.id)
        return list(self.db.scalars(query).unique())
