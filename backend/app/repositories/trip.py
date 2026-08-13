from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import Trip
from app.repositories.base import BaseRepository


class TripRepository(BaseRepository[Trip]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Trip)

    def _base_query(self):
        return (
            select(Trip)
            .options(selectinload(Trip.status_history), selectinload(Trip.ride_request))
            .execution_options(populate_existing=True)
        )

    def get(self, entity_id: UUID):  # type: ignore[override]
        return self.db.scalar(self._base_query().where(Trip.id == entity_id))

    def get_by_ride_request_id(self, ride_request_id: UUID) -> Trip | None:
        return self.db.scalar(self._base_query().where(Trip.ride_request_id == ride_request_id))

    def list_for_driver(self, driver_id: UUID) -> list[Trip]:
        query = self._base_query().where(Trip.driver_id == driver_id).order_by(Trip.updated_at.desc())
        return list(self.db.scalars(query))
