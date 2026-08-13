from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from app.models.domain import DriverAvailability, RideRequest, User
from app.models.enums import AvailabilityStatus, RideRequestStatus, UserRole
from app.repositories.driver_availability import DriverAvailabilityRepository
from app.repositories.ride_request import RideRequestRepository
from app.services.background_task import BackgroundTaskService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.operational_event import OperationalEventService, OperationalEventType
from app.services.trip import TripService


class DriverMatchingService:
    def __init__(
        self,
        db: Session,
        event_service: OperationalEventService | None = None,
        background_task_service: BackgroundTaskService | None = None,
    ) -> None:
        self.db = db
        self.driver_availability_repository = DriverAvailabilityRepository(db)
        self.ride_request_repository = RideRequestRepository(db)
        self.event_service = event_service if event_service is not None else OperationalEventService()
        self.background_task_service = (
            background_task_service
            if background_task_service is not None
            else BackgroundTaskService(event_service=self.event_service)
        )
        self.trip_service = TripService(
            db,
            event_service=self.event_service,
            background_task_service=self.background_task_service,
        )

    def mark_ride_request_as_searching(self, ride_request_id) -> RideRequest:
        ride_request = self.ride_request_repository.get(ride_request_id)
        if ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")

        if ride_request.status in {RideRequestStatus.CANCELLED, RideRequestStatus.DRIVER_ASSIGNED}:
            return ride_request

        ride_request.status = RideRequestStatus.SEARCHING_DRIVER
        self.db.add(ride_request)
        self.db.commit()
        self.db.refresh(ride_request)
        self.background_task_service.dispatch_operational_event(
            OperationalEventType.DRIVER_SEARCH_STARTED,
            ride_id=ride_request.id,
            actor_id=ride_request.rider.user_id,
            metadata={"status": ride_request.status.value},
        )
        return ride_request

    def list_ride_offers_for_driver(self, current_user: User) -> list[RideRequest]:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None:
            raise ResourceConflictError("Only drivers can view ride offers.")

        availability = self.driver_availability_repository.get_latest_for_driver(driver.id)
        if availability is None or availability.status != AvailabilityStatus.AVAILABLE:
            return []

        offers = self.ride_request_repository.list_by_status(RideRequestStatus.SEARCHING_DRIVER)
        offers.sort(key=lambda offer: self._distance_to_pickup_km(availability, offer))
        return offers

    def accept_ride_offer(self, ride_request_id, current_user: User) -> RideRequest:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None:
            raise ResourceConflictError("Only drivers can accept ride offers.")

        availability = self.driver_availability_repository.get_latest_for_driver(driver.id)
        if availability is None or availability.status != AvailabilityStatus.AVAILABLE:
            raise ResourceConflictError("Driver must be AVAILABLE before accepting a ride offer.")

        reserved = self.driver_availability_repository.reserve_if_available(availability.id)
        if not reserved:
            raise ResourceConflictError("Driver is no longer available for ride selection.")

        claimed = self.ride_request_repository.claim_driver_if_searching(ride_request_id, driver.id)
        if not claimed:
            availability.status = AvailabilityStatus.AVAILABLE
            self.driver_availability_repository.save(availability)
            raise ResourceConflictError("Ride offer is no longer available.")

        refreshed_ride_request = self.ride_request_repository.get(ride_request_id)
        if refreshed_ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")

        self.background_task_service.dispatch_operational_event(
            OperationalEventType.DRIVER_ASSIGNED,
            ride_id=refreshed_ride_request.id,
            actor_id=current_user.id,
            metadata={
                "driver_id": driver.id,
                "status": refreshed_ride_request.status.value,
            },
        )
        self.background_task_service.dispatch_rider_notification(
            refreshed_ride_request.rider.user_id,
            "DRIVER_ASSIGNED",
            {
                "ride_id": str(refreshed_ride_request.id),
                "driver_id": str(driver.id),
                "status": refreshed_ride_request.status.value,
            },
        )
        self.background_task_service.dispatch_driver_notification(
            current_user.id,
            "RIDE_ASSIGNED",
            {"ride_id": str(refreshed_ride_request.id), "status": refreshed_ride_request.status.value},
        )
        self.trip_service.create_trip_for_assigned_ride(
            refreshed_ride_request,
            changed_by=current_user.id,
        )
        updated_ride_request = self.ride_request_repository.get(ride_request_id)
        if updated_ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")
        return updated_ride_request

    @staticmethod
    def _distance_to_pickup_km(availability: DriverAvailability, ride_request: RideRequest) -> float:
        return haversine_km(
            availability.latitude,
            availability.longitude,
            ride_request.pickup_latitude,
            ride_request.pickup_longitude,
        )


def haversine_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    earth_radius_km = 6371.0

    lat_a = radians(latitude_a)
    lon_a = radians(longitude_a)
    lat_b = radians(latitude_b)
    lon_b = radians(longitude_b)

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a

    haversine_value = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    central_angle = 2 * asin(sqrt(haversine_value))

    return earth_radius_km * central_angle
