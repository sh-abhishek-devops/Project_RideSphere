from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.domain import RideRequest, Trip
from app.models.enums import RideRequestStatus
from app.repositories.base import BaseRepository


class RideRequestRepository(BaseRepository[RideRequest]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RideRequest)

    def _base_query(self):
        return select(RideRequest).options(
            selectinload(RideRequest.trip).selectinload(Trip.status_history)
        )

    def get(self, entity_id: UUID):  # type: ignore[override]
        return self.db.scalar(self._base_query().where(RideRequest.id == entity_id))

    def list_for_rider(self, rider_id: UUID) -> list[RideRequest]:
        query = self._base_query().where(RideRequest.rider_id == rider_id).order_by(RideRequest.requested_at.desc())
        return list(self.db.scalars(query))

    def list_by_status(self, status: RideRequestStatus) -> list[RideRequest]:
        query = self._base_query().where(RideRequest.status == status).order_by(RideRequest.requested_at.asc())
        return list(self.db.scalars(query))

    def claim_driver_if_searching(self, ride_id: UUID, driver_id: UUID) -> bool:
        result = self.db.execute(
            update(RideRequest)
            .where(
                RideRequest.id == ride_id,
                RideRequest.status == RideRequestStatus.SEARCHING_DRIVER,
                RideRequest.driver_id.is_(None),
            )
            .values(driver_id=driver_id, status=RideRequestStatus.DRIVER_ASSIGNED)
        )
        self.db.commit()
        return result.rowcount == 1
