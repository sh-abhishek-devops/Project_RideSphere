from uuid import UUID

from sqlalchemy.orm import Session

from app.models.domain import DriverAvailability, User
from app.models.enums import AvailabilityStatus, UserRole
from app.repositories.driver import DriverRepository
from app.repositories.driver_availability import DriverAvailabilityRepository
from app.schemas.driver_availability import DriverAvailabilityCreate, DriverSelfAvailabilityUpdate
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError


class DriverAvailabilityService:
    def __init__(self, db: Session) -> None:
        self.driver_repository = DriverRepository(db)
        self.driver_availability_repository = DriverAvailabilityRepository(db)

    def create_driver_availability(self, payload: DriverAvailabilityCreate) -> DriverAvailability:
        if self.driver_repository.get(payload.driver_id) is None:
            raise ResourceNotFoundError("Driver not found.")

        availability = DriverAvailability(**payload.model_dump())
        return self.driver_availability_repository.create(availability)

    def get_driver_availability(self, availability_id: UUID):
        return self.driver_availability_repository.get(availability_id)

    def list_driver_availabilities(self) -> list[DriverAvailability]:
        return self.driver_availability_repository.list()

    def update_my_availability(
        self,
        current_user: User,
        payload: DriverSelfAvailabilityUpdate,
    ) -> DriverAvailability:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None:
            raise ResourceConflictError("Only drivers can modify driver availability.")

        if payload.status not in {AvailabilityStatus.OFFLINE, AvailabilityStatus.AVAILABLE}:
            raise ResourceConflictError("Drivers can only set availability to OFFLINE or AVAILABLE.")

        availability = self.driver_availability_repository.get_latest_for_driver(driver.id)
        if availability is None:
            availability = DriverAvailability(
                driver_id=driver.id,
                status=payload.status,
                latitude=payload.latitude,
                longitude=payload.longitude,
            )
        else:
            availability.status = payload.status
            availability.latitude = payload.latitude
            availability.longitude = payload.longitude

        return self.driver_availability_repository.save(availability)

    def get_my_availability(self, current_user: User) -> DriverAvailability:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None:
            raise ResourceConflictError("Only drivers can view driver availability.")

        availability = self.driver_availability_repository.get_latest_for_driver(driver.id)
        if availability is None:
            availability = DriverAvailability(
                driver_id=driver.id,
                status=AvailabilityStatus.OFFLINE,
                latitude=0.0,
                longitude=0.0,
            )
            return self.driver_availability_repository.save(availability)
        return availability
