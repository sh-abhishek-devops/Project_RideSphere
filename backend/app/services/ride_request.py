from uuid import UUID

from sqlalchemy.orm import Session

from app.models.domain import RideRequest, User
from app.models.enums import RideRequestStatus, UserRole
from app.repositories.ride_request import RideRequestRepository
from app.schemas.ride_request import RideRequestCreate
from app.services.background_task import BackgroundTaskService
from app.services.driver_matching import DriverMatchingService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.operational_event import OperationalEventService, OperationalEventType
from app.services.trip import TripService

PRIVILEGED_RIDE_ROLES = {
    UserRole.SUPPORT_AGENT,
    UserRole.PAYMENT_AGENT,
    UserRole.OPERATIONS_MANAGER,
    UserRole.ADMIN,
}


class RideRequestService:
    def __init__(self, db: Session, event_service: OperationalEventService | None = None) -> None:
        self.db = db
        self.ride_request_repository = RideRequestRepository(db)
        self.event_service = event_service if event_service is not None else OperationalEventService()
        self.background_task_service = BackgroundTaskService(event_service=self.event_service)
        self.driver_matching_service = DriverMatchingService(
            db,
            event_service=self.event_service,
            background_task_service=self.background_task_service,
        )
        self.trip_service = TripService(
            db,
            event_service=self.event_service,
            background_task_service=self.background_task_service,
        )

    def create_ride_request(self, current_user: User, payload: RideRequestCreate) -> RideRequest:
        rider = current_user.rider_profile
        if current_user.role != UserRole.RIDER or rider is None:
            raise ResourceConflictError("Only riders can request rides.")

        ride_request = RideRequest(
            rider_id=rider.id,
            driver_id=None,
            pickup_address=payload.pickup_address,
            pickup_latitude=payload.pickup_latitude,
            pickup_longitude=payload.pickup_longitude,
            destination_address=payload.destination_address,
            destination_latitude=payload.destination_latitude,
            destination_longitude=payload.destination_longitude,
            ride_type=payload.ride_type,
            status=RideRequestStatus.REQUESTED,
            estimated_distance=payload.estimated_distance,
            estimated_duration=payload.estimated_duration,
        )
        ride_request = self.ride_request_repository.create(ride_request)
        self.background_task_service.dispatch_operational_event(
            OperationalEventType.RIDE_REQUESTED,
            ride_id=ride_request.id,
            actor_id=current_user.id,
            metadata={
                "ride_type": ride_request.ride_type.value,
                "estimated_distance": ride_request.estimated_distance,
                "estimated_duration": ride_request.estimated_duration,
                "status": ride_request.status.value,
            },
        )
        self.background_task_service.dispatch_rider_notification(
            current_user.id,
            "RIDE_REQUESTED",
            {"ride_id": str(ride_request.id), "status": ride_request.status.value},
        )
        return self.driver_matching_service.mark_ride_request_as_searching(ride_request.id)

    def get_ride_request(self, ride_id: UUID, current_user: User) -> RideRequest:
        ride_request = self.ride_request_repository.get(ride_id)
        if ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")
        self._assert_can_access(current_user, ride_request)
        return ride_request

    def list_ride_requests(self, current_user: User) -> list[RideRequest]:
        if current_user.role in PRIVILEGED_RIDE_ROLES:
            return self.ride_request_repository.list()

        rider = current_user.rider_profile
        if current_user.role != UserRole.RIDER or rider is None:
            raise ResourceConflictError("Only riders or privileged users can view ride requests.")
        return self.ride_request_repository.list_for_rider(rider.id)

    def list_driver_ride_offers(self, current_user: User) -> list[RideRequest]:
        return self.driver_matching_service.list_ride_offers_for_driver(current_user)

    def accept_driver_ride_offer(self, ride_id: UUID, current_user: User) -> RideRequest:
        return self.driver_matching_service.accept_ride_offer(ride_id, current_user)

    def cancel_ride_request(self, ride_id: UUID, current_user: User) -> RideRequest:
        ride_request = self.get_ride_request(ride_id, current_user)

        if ride_request.status == RideRequestStatus.CANCELLED:
            raise ResourceConflictError("Ride request is already cancelled.")

        ride_request.status = RideRequestStatus.CANCELLED
        self.db.add(ride_request)
        self.db.commit()
        self.trip_service.cancel_trip_for_ride_request(ride_request, changed_by=current_user.id)
        self.db.refresh(ride_request)
        self.background_task_service.dispatch_operational_event(
            OperationalEventType.RIDE_CANCELLED,
            ride_id=ride_request.id,
            actor_id=current_user.id,
            metadata={"status": ride_request.status.value},
        )
        return ride_request

    def _assert_can_access(self, current_user: User, ride_request: RideRequest) -> None:
        if current_user.role in PRIVILEGED_RIDE_ROLES:
            return

        rider = current_user.rider_profile
        if current_user.role == UserRole.RIDER and rider is not None and ride_request.rider_id == rider.id:
            return

        raise ResourceNotFoundError("Ride request not found.")
