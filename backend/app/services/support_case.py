from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.domain import SupportCase, User
from app.models.enums import SupportCaseStatus, UserRole
from app.repositories.driver import DriverRepository
from app.repositories.payment import PaymentRepository
from app.repositories.ride_request import RideRequestRepository
from app.repositories.rider import RiderRepository
from app.repositories.support_case import SupportCaseRepository
from app.repositories.trip import TripRepository
from app.repositories.user import UserRepository
from app.repositories.vehicle import VehicleRepository
from app.schemas.support_case import (
    SupportAgentSummary,
    SupportCaseCreate,
    SupportCaseResolve,
    SupportCaseUpdate,
    SupportInvestigationResponse,
)
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.operational_event import OperationalEventService, OperationalEventType
from app.services.payment import PaymentService

SUPPORT_CASE_ACCESS_ROLES = {
    UserRole.SUPPORT_AGENT,
    UserRole.PAYMENT_AGENT,
    UserRole.OPERATIONS_MANAGER,
    UserRole.ADMIN,
}

ASSIGNABLE_SUPPORT_ROLES = SUPPORT_CASE_ACCESS_ROLES


class SupportCaseService:
    def __init__(self, db: Session, event_service: OperationalEventService | None = None) -> None:
        self.db = db
        self.support_case_repository = SupportCaseRepository(db)
        self.ride_request_repository = RideRequestRepository(db)
        self.trip_repository = TripRepository(db)
        self.rider_repository = RiderRepository(db)
        self.driver_repository = DriverRepository(db)
        self.vehicle_repository = VehicleRepository(db)
        self.user_repository = UserRepository(db)
        self.payment_repository = PaymentRepository(db)
        self.payment_service = PaymentService(db, event_service=event_service)
        self.event_service = event_service if event_service is not None else OperationalEventService()

    def list_support_cases(self, current_user: User) -> list[SupportCase]:
        self._assert_can_access(current_user)
        return self.support_case_repository.list()

    def get_support_case(self, case_id: UUID, current_user: User) -> SupportCase:
        self._assert_can_access(current_user)
        case = self.support_case_repository.get(case_id)
        if case is None:
            raise ResourceNotFoundError("Support case not found.")
        return case

    def list_assignable_agents(self, current_user: User) -> list[SupportAgentSummary]:
        self._assert_can_access(current_user)
        agents = [
            user
            for user in self.user_repository.list()
            if user.role in ASSIGNABLE_SUPPORT_ROLES and user.is_active
        ]
        return [
            SupportAgentSummary(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active,
            )
            for user in agents
        ]

    def create_support_case(self, current_user: User, payload: SupportCaseCreate) -> SupportCase:
        self._assert_can_access(current_user)
        ride_request = self.ride_request_repository.get(payload.ride_request_id)
        if ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")

        assigned_agent_user_id = self._validate_assigned_agent(payload.assigned_agent_user_id)
        trip = self.trip_repository.get_by_ride_request_id(ride_request.id)
        status = SupportCaseStatus.ASSIGNED if assigned_agent_user_id is not None else SupportCaseStatus.OPEN

        support_case = SupportCase(
            ride_request_id=ride_request.id,
            trip_id=trip.id if trip is not None else None,
            created_by_user_id=current_user.id,
            assigned_agent_user_id=assigned_agent_user_id,
            issue_summary=payload.issue_summary,
            priority=payload.priority,
            status=status,
            resolution_notes=None,
            resolved_at=None,
        )
        support_case = self.support_case_repository.create(support_case)
        self.event_service.publish(
            OperationalEventType.SUPPORT_CASE_CREATED,
            ride_id=support_case.ride_request_id,
            trip_id=support_case.trip_id,
            actor_id=current_user.id,
            metadata={
                "support_case_id": support_case.id,
                "priority": support_case.priority.value,
                "status": support_case.status.value,
            },
        )
        refreshed_case = self.support_case_repository.get(support_case.id)
        if refreshed_case is None:
            raise ResourceNotFoundError("Support case not found.")
        return refreshed_case

    def update_support_case(self, case_id: UUID, current_user: User, payload: SupportCaseUpdate) -> SupportCase:
        support_case = self.get_support_case(case_id, current_user)
        update_data = payload.model_dump(exclude_unset=True)

        if "assigned_agent_user_id" in update_data:
            support_case.assigned_agent_user_id = self._validate_assigned_agent(payload.assigned_agent_user_id)
            if support_case.assigned_agent_user_id is not None and support_case.status == SupportCaseStatus.OPEN:
                support_case.status = SupportCaseStatus.ASSIGNED

        if payload.priority is not None:
            support_case.priority = payload.priority

        if payload.status is not None:
            if payload.status == SupportCaseStatus.RESOLVED:
                raise ResourceConflictError("Use the resolve endpoint to mark a support case as resolved.")
            support_case.status = payload.status

        if "resolution_notes" in update_data:
            support_case.resolution_notes = payload.resolution_notes

        self._refresh_case_trip_link(support_case)
        self.db.add(support_case)
        self.db.commit()
        refreshed_case = self.support_case_repository.get(support_case.id)
        if refreshed_case is None:
            raise ResourceNotFoundError("Support case not found.")
        return refreshed_case

    def resolve_support_case(self, case_id: UUID, current_user: User, payload: SupportCaseResolve) -> SupportCase:
        support_case = self.get_support_case(case_id, current_user)
        support_case.status = SupportCaseStatus.RESOLVED
        support_case.resolution_notes = payload.resolution_notes
        support_case.resolved_at = datetime.now(UTC)
        self._refresh_case_trip_link(support_case)
        self.db.add(support_case)
        self.db.commit()
        refreshed_case = self.support_case_repository.get(support_case.id)
        if refreshed_case is None:
            raise ResourceNotFoundError("Support case not found.")
        return refreshed_case

    def get_investigation(self, case_id: UUID, current_user: User) -> SupportInvestigationResponse:
        support_case = self.get_support_case(case_id, current_user)
        ride_request = self.ride_request_repository.get(support_case.ride_request_id)
        if ride_request is None:
            raise ResourceNotFoundError("Ride request not found.")

        rider = self.rider_repository.get(ride_request.rider_id)
        if rider is None:
            raise ResourceNotFoundError("Rider not found.")

        trip = self.trip_repository.get(support_case.trip_id) if support_case.trip_id is not None else None
        if trip is None:
            trip = self.trip_repository.get_by_ride_request_id(ride_request.id)
            if trip is not None and support_case.trip_id != trip.id:
                support_case.trip_id = trip.id
                self.db.add(support_case)
                self.db.commit()
                support_case = self.get_support_case(case_id, current_user)

        driver = self.driver_repository.get(ride_request.driver_id) if ride_request.driver_id is not None else None
        vehicle = self.vehicle_repository.get(trip.vehicle_id) if trip is not None and trip.vehicle_id is not None else None

        payment = None
        if trip is not None:
            payment_record = self.payment_repository.get_by_trip_id(trip.id)
            if payment_record is not None:
                payment = self.payment_service.get_trip_payment(trip.id, current_user)

        return SupportInvestigationResponse(
            case=support_case,
            rider=rider,
            driver=driver,
            vehicle=vehicle,
            ride_request=ride_request,
            trip=trip,
            payment=payment,
        )

    @staticmethod
    def _assert_can_access(current_user: User) -> None:
        if current_user.role not in SUPPORT_CASE_ACCESS_ROLES:
            raise ResourceConflictError("You are not allowed to access support cases.")

    def _validate_assigned_agent(self, assigned_agent_user_id: UUID | None) -> UUID | None:
        if assigned_agent_user_id is None:
            return None

        user = self.user_repository.get(assigned_agent_user_id)
        if user is None:
            raise ResourceNotFoundError("Assigned agent not found.")
        if user.role not in ASSIGNABLE_SUPPORT_ROLES or not user.is_active:
            raise ResourceConflictError("Assigned user is not eligible for support case assignment.")
        return user.id

    def _refresh_case_trip_link(self, support_case: SupportCase) -> None:
        if support_case.trip_id is None:
            trip = self.trip_repository.get_by_ride_request_id(support_case.ride_request_id)
            if trip is not None:
                support_case.trip_id = trip.id
