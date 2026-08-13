from datetime import UTC, datetime
from secrets import randbelow
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.domain import DriverAvailability, RideRequest, Trip, TripStatusHistory, User
from app.models.enums import AvailabilityStatus, TripStatus, UserRole
from app.repositories.driver_availability import DriverAvailabilityRepository
from app.repositories.trip import TripRepository
from app.repositories.trip_status_history import TripStatusHistoryRepository
from app.repositories.vehicle import VehicleRepository
from app.services.background_task import BackgroundTaskService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.operational_event import OperationalEventService, OperationalEventType
from app.services.payment import PaymentService

PRIVILEGED_TRIP_ROLES = {
    UserRole.SUPPORT_AGENT,
    UserRole.PAYMENT_AGENT,
    UserRole.OPERATIONS_MANAGER,
    UserRole.ADMIN,
}

ALLOWED_TRIP_TRANSITIONS = {
    TripStatus.DRIVER_ASSIGNED: {TripStatus.DRIVER_EN_ROUTE, TripStatus.CANCELLED},
    TripStatus.DRIVER_EN_ROUTE: {TripStatus.DRIVER_ARRIVED, TripStatus.CANCELLED},
    TripStatus.DRIVER_ARRIVED: {TripStatus.TRIP_STARTED, TripStatus.CANCELLED},
    TripStatus.TRIP_STARTED: {TripStatus.TRIP_COMPLETED},
}


TRIP_STATUS_EVENT_MAP = {
    TripStatus.DRIVER_EN_ROUTE: OperationalEventType.DRIVER_EN_ROUTE,
    TripStatus.DRIVER_ARRIVED: OperationalEventType.DRIVER_ARRIVED,
    TripStatus.TRIP_STARTED: OperationalEventType.TRIP_STARTED,
    TripStatus.TRIP_COMPLETED: OperationalEventType.TRIP_COMPLETED,
}


class TripService:
    def __init__(
        self,
        db: Session,
        event_service: OperationalEventService | None = None,
        background_task_service: BackgroundTaskService | None = None,
    ) -> None:
        self.db = db
        self.trip_repository = TripRepository(db)
        self.trip_status_history_repository = TripStatusHistoryRepository(db)
        self.driver_availability_repository = DriverAvailabilityRepository(db)
        self.vehicle_repository = VehicleRepository(db)
        self.event_service = event_service if event_service is not None else OperationalEventService()
        self.background_task_service = (
            background_task_service
            if background_task_service is not None
            else BackgroundTaskService(event_service=self.event_service)
        )
        self.payment_service = PaymentService(
            db,
            event_service=self.event_service,
            background_task_service=self.background_task_service,
        )

    def create_trip_for_assigned_ride(self, ride_request: RideRequest, changed_by: UUID) -> Trip:
        existing_trip = self.trip_repository.get_by_ride_request_id(ride_request.id)
        if existing_trip is not None:
            return existing_trip
        if ride_request.driver_id is None:
            raise ResourceConflictError("Cannot create trip without an assigned driver.")

        vehicle = self.vehicle_repository.get_active_for_driver(ride_request.driver_id)
        trip = Trip(
            ride_request_id=ride_request.id,
            rider_id=ride_request.rider_id,
            driver_id=ride_request.driver_id,
            vehicle_id=vehicle.id if vehicle is not None else None,
            status=TripStatus.DRIVER_ASSIGNED,
            rider_start_pin=self._generate_rider_start_pin(),
        )
        self.db.add(trip)
        self.db.flush()
        self.db.add(
            TripStatusHistory(
                trip_id=trip.id,
                previous_status=None,
                new_status=TripStatus.DRIVER_ASSIGNED,
                changed_by=changed_by,
            )
        )
        self.db.commit()
        refreshed_trip = self.trip_repository.get(trip.id)
        if refreshed_trip is None:
            raise ResourceNotFoundError("Trip not found.")
        return refreshed_trip

    def get_trip(self, trip_id: UUID, current_user: User) -> Trip:
        trip = self.trip_repository.get(trip_id)
        if trip is None:
            raise ResourceNotFoundError("Trip not found.")
        self._assert_can_access(current_user, trip)
        return trip

    def list_driver_trips(self, current_user: User) -> list[Trip]:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None:
            raise ResourceConflictError("Only drivers can view driver trips.")
        return self.trip_repository.list_for_driver(driver.id)

    def mark_en_route(self, trip_id: UUID, current_user: User) -> Trip:
        return self._transition_trip(trip_id, current_user, TripStatus.DRIVER_EN_ROUTE)

    def mark_arrived(self, trip_id: UUID, current_user: User) -> Trip:
        return self._transition_trip(trip_id, current_user, TripStatus.DRIVER_ARRIVED)

    def start_trip(self, trip_id: UUID, current_user: User, rider_start_pin: str) -> Trip:
        trip = self.trip_repository.get(trip_id)
        if trip is None:
            raise ResourceNotFoundError("Trip not found.")
        self._assert_driver_controls_trip(current_user, trip)
        if trip.rider_start_pin != rider_start_pin:
            raise ResourceConflictError("Rider PIN does not match.")
        return self._apply_transition(trip, TripStatus.TRIP_STARTED, current_user.id)

    def complete_trip(
        self,
        trip_id: UUID,
        current_user: User,
        actual_distance: float,
        actual_duration: int,
    ) -> Trip:
        return self._transition_trip(
            trip_id,
            current_user,
            TripStatus.TRIP_COMPLETED,
            actual_distance=actual_distance,
            actual_duration=actual_duration,
        )

    def cancel_trip_for_ride_request(self, ride_request: RideRequest, changed_by: UUID) -> Trip | None:
        trip = self.trip_repository.get_by_ride_request_id(ride_request.id)
        if trip is None or trip.status in {TripStatus.TRIP_COMPLETED, TripStatus.CANCELLED}:
            return trip
        return self._apply_transition(trip, TripStatus.CANCELLED, changed_by)

    def _transition_trip(
        self,
        trip_id: UUID,
        current_user: User,
        new_status: TripStatus,
        actual_distance: float | None = None,
        actual_duration: int | None = None,
    ) -> Trip:
        trip = self.trip_repository.get(trip_id)
        if trip is None:
            raise ResourceNotFoundError("Trip not found.")
        self._assert_driver_controls_trip(current_user, trip)
        return self._apply_transition(
            trip,
            new_status,
            current_user.id,
            actual_distance=actual_distance,
            actual_duration=actual_duration,
        )

    def _apply_transition(
        self,
        trip: Trip,
        new_status: TripStatus,
        changed_by: UUID,
        actual_distance: float | None = None,
        actual_duration: int | None = None,
    ) -> Trip:
        allowed = ALLOWED_TRIP_TRANSITIONS.get(trip.status, set())
        if new_status not in allowed:
            raise ResourceConflictError(f"Cannot transition trip from {trip.status} to {new_status}.")

        previous_status = trip.status
        trip.status = new_status

        if new_status == TripStatus.TRIP_STARTED:
            trip.started_at = datetime.now(UTC)
            self._set_driver_availability(trip.driver_id, AvailabilityStatus.ON_TRIP)
        elif new_status == TripStatus.TRIP_COMPLETED:
            trip.completed_at = datetime.now(UTC)
            trip.actual_distance = actual_distance
            trip.actual_duration = actual_duration
            self._set_driver_availability(trip.driver_id, AvailabilityStatus.AVAILABLE)
        elif new_status == TripStatus.CANCELLED:
            self._set_driver_availability(trip.driver_id, AvailabilityStatus.AVAILABLE)

        self.db.add(trip)
        self.db.add(
            TripStatusHistory(
                trip_id=trip.id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
            )
        )
        self.db.commit()
        refreshed_trip = self.trip_repository.get(trip.id)
        if refreshed_trip is None:
            raise ResourceNotFoundError("Trip not found.")
        event_type = TRIP_STATUS_EVENT_MAP.get(new_status)
        if event_type is not None:
            self.background_task_service.dispatch_operational_event(
                event_type,
                ride_id=refreshed_trip.ride_request_id,
                trip_id=refreshed_trip.id,
                actor_id=changed_by,
                metadata={
                    "previous_status": previous_status.value,
                    "new_status": new_status.value,
                    "actual_distance": actual_distance,
                    "actual_duration": actual_duration,
                },
            )
            self.background_task_service.dispatch_rider_notification(
                refreshed_trip.rider.user_id,
                new_status.value,
                {"trip_id": str(refreshed_trip.id), "status": new_status.value},
            )
            self.background_task_service.dispatch_driver_notification(
                refreshed_trip.driver.user_id,
                new_status.value,
                {"trip_id": str(refreshed_trip.id), "status": new_status.value},
            )
        if new_status == TripStatus.TRIP_COMPLETED:
            self.payment_service.create_payment_for_completed_trip(refreshed_trip)
            refreshed_trip = self.trip_repository.get(trip.id)
            if refreshed_trip is None:
                raise ResourceNotFoundError("Trip not found.")
        return refreshed_trip

    def _set_driver_availability(self, driver_id: UUID, status: AvailabilityStatus) -> None:
        availability = self.driver_availability_repository.get_latest_for_driver(driver_id)
        if availability is None:
            availability = DriverAvailability(driver_id=driver_id, status=status, latitude=0.0, longitude=0.0)
        else:
            availability.status = status
        self.db.add(availability)

    @staticmethod
    def _generate_rider_start_pin() -> str:
        return f"{randbelow(1_000_000):06d}"

    @staticmethod
    def _assert_driver_controls_trip(current_user: User, trip: Trip) -> None:
        driver = current_user.driver_profile
        if current_user.role != UserRole.DRIVER or driver is None or trip.driver_id != driver.id:
            raise ResourceConflictError("Only the assigned driver can update this trip.")

    @staticmethod
    def _assert_can_access(current_user: User, trip: Trip) -> None:
        if current_user.role in PRIVILEGED_TRIP_ROLES:
            return
        rider = current_user.rider_profile
        if current_user.role == UserRole.RIDER and rider is not None and trip.rider_id == rider.id:
            return
        driver = current_user.driver_profile
        if current_user.role == UserRole.DRIVER and driver is not None and trip.driver_id == driver.id:
            return
        raise ResourceNotFoundError("Trip not found.")
