from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.domain import DriverAvailability
from app.models.enums import AvailabilityStatus
from app.repositories.base import BaseRepository


class DriverAvailabilityRepository(BaseRepository[DriverAvailability]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, DriverAvailability)

    def get_latest_for_driver(self, driver_id):
        query = (
            select(DriverAvailability)
            .where(DriverAvailability.driver_id == driver_id)
            .order_by(DriverAvailability.updated_at.desc(), DriverAvailability.id.desc())
            .limit(1)
        )
        return self.db.scalar(query)

    def save(self, availability: DriverAvailability) -> DriverAvailability:
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        return availability

    def list_latest_by_driver(self) -> list[DriverAvailability]:
        query = select(DriverAvailability).order_by(
            DriverAvailability.driver_id,
            DriverAvailability.updated_at.desc(),
            DriverAvailability.id.desc(),
        )
        records = list(self.db.scalars(query))
        latest: dict = {}
        for record in records:
            latest.setdefault(record.driver_id, record)
        return list(latest.values())

    def reserve_if_available(self, availability_id) -> bool:
        result = self.db.execute(
            update(DriverAvailability)
            .where(
                DriverAvailability.id == availability_id,
                DriverAvailability.status == AvailabilityStatus.AVAILABLE,
            )
            .values(status=AvailabilityStatus.RESERVED, updated_at=func.now())
        )
        self.db.commit()
        return result.rowcount == 1
