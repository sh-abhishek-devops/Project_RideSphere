from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Vehicle
from app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Vehicle)

    def get_active_for_driver(self, driver_id):
        query = (
            select(Vehicle)
            .where(Vehicle.driver_id == driver_id, Vehicle.is_active.is_(True))
            .order_by(Vehicle.id.asc())
            .limit(1)
        )
        return self.db.scalar(query)
