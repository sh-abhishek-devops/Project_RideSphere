from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.domain import Vehicle
from app.repositories.driver import DriverRepository
from app.repositories.vehicle import VehicleRepository
from app.schemas.vehicle import VehicleCreate
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError


class VehicleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.vehicle_repository = VehicleRepository(db)
        self.driver_repository = DriverRepository(db)

    def create_vehicle(self, payload: VehicleCreate) -> Vehicle:
        if self.driver_repository.get(payload.driver_id) is None:
            raise ResourceNotFoundError("Driver not found.")

        vehicle = Vehicle(**payload.model_dump())

        try:
            return self.vehicle_repository.create(vehicle)
        except IntegrityError as exc:
            self.db.rollback()
            raise ResourceConflictError("Vehicle with this license plate already exists.") from exc

    def get_vehicle(self, vehicle_id: UUID):
        return self.vehicle_repository.get(vehicle_id)

    def list_vehicles(self) -> list[Vehicle]:
        return self.vehicle_repository.list()
