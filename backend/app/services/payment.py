from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import Payment, Trip, User
from app.models.enums import PaymentStatus, TripStatus, UserRole
from app.repositories.payment import PaymentRepository
from app.repositories.trip import TripRepository
from app.schemas.payment import PaymentResponse
from app.services.background_task import BackgroundTaskService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.notification import NotificationService
from app.services.operational_event import OperationalEventService, OperationalEventType

PAYMENT_ACCESS_ROLES = {
    UserRole.SUPPORT_AGENT,
    UserRole.PAYMENT_AGENT,
    UserRole.OPERATIONS_MANAGER,
    UserRole.ADMIN,
}
PAYMENT_REFUND_ROLES = {
    UserRole.PAYMENT_AGENT,
    UserRole.OPERATIONS_MANAGER,
    UserRole.ADMIN,
}


class MockPaymentProvider:
    @staticmethod
    def process(payment: Payment) -> Payment:
        payment.status = PaymentStatus.PROCESSING
        payment.status = PaymentStatus.SUCCESS
        return payment


class PaymentService:
    def __init__(
        self,
        db: Session,
        event_service: OperationalEventService | None = None,
        notification_service: NotificationService | None = None,
        background_task_service: BackgroundTaskService | None = None,
    ) -> None:
        self.db = db
        self.settings = get_settings()
        self.payment_repository = PaymentRepository(db)
        self.trip_repository = TripRepository(db)
        self.provider = MockPaymentProvider()
        self.event_service = event_service if event_service is not None else OperationalEventService()
        self.notification_service = (
            notification_service if notification_service is not None else NotificationService()
        )
        self.background_task_service = (
            background_task_service
            if background_task_service is not None
            else BackgroundTaskService(
                event_service=self.event_service,
                notification_service=self.notification_service,
            )
        )

    def create_payment_for_completed_trip(self, trip: Trip) -> Payment:
        if trip.status != TripStatus.TRIP_COMPLETED:
            raise ResourceConflictError("Payments can only be created for completed trips.")

        existing_payment = self.payment_repository.get_by_trip_id(trip.id)
        if existing_payment is not None:
            return existing_payment

        payment = Payment(
            trip_id=trip.id,
            rider_id=trip.rider_id,
            amount=self.calculate_fare(trip),
            currency=self.settings.payment_currency,
            status=PaymentStatus.PENDING,
            payment_reference=self._build_payment_reference(trip.id),
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        self.background_task_service.dispatch_operational_event(
            OperationalEventType.PAYMENT_CREATED,
            ride_id=trip.ride_request_id,
            trip_id=trip.id,
            actor_id=None,
            metadata={
                "payment_id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status.value,
            },
        )
        self.background_task_service.dispatch_payment_processing(payment.id)
        self.db.expire_all()
        refreshed_payment = self.payment_repository.get(payment.id)
        if refreshed_payment is None:
            raise ResourceNotFoundError("Payment not found.")
        return refreshed_payment

    def get_payment(self, payment_id: UUID, current_user: User):
        payment = self.payment_repository.get(payment_id)
        if payment is None:
            raise ResourceNotFoundError("Payment not found.")
        self._assert_can_access(current_user, payment)
        return self._serialize_for_user(payment, current_user)

    def get_trip_payment(self, trip_id: UUID, current_user: User):
        payment = self.payment_repository.get_by_trip_id(trip_id)
        if payment is None:
            trip = self.trip_repository.get(trip_id)
            if trip is None:
                raise ResourceNotFoundError("Trip not found.")
            self._assert_can_access_trip(current_user, trip)
            raise ResourceNotFoundError("Payment not found.")
        self._assert_can_access(current_user, payment)
        return self._serialize_for_user(payment, current_user)

    def refund_payment(self, payment_id: UUID, current_user: User):
        payment = self.payment_repository.get(payment_id)
        if payment is None:
            raise ResourceNotFoundError("Payment not found.")
        self._assert_can_refund(current_user)

        if payment.status == PaymentStatus.REFUNDED:
            return self._serialize_for_user(payment, current_user)
        if payment.status != PaymentStatus.SUCCESS:
            raise ResourceConflictError("Only successful payments can be refunded.")

        payment.status = PaymentStatus.REFUNDED
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        self.event_service.publish(
            OperationalEventType.REFUND_CREATED,
            ride_id=payment.trip.ride_request_id,
            trip_id=payment.trip_id,
            actor_id=current_user.id,
            metadata={
                "payment_id": payment.id,
                "currency": payment.currency,
                "status": payment.status.value,
            },
        )
        return self._serialize_for_user(payment, current_user)

    def process_pending_payment(self, payment_id: UUID) -> Payment:
        payment = self.payment_repository.get(payment_id)
        if payment is None:
            raise ResourceNotFoundError("Payment not found.")

        if payment.status in {PaymentStatus.SUCCESS, PaymentStatus.REFUNDED}:
            return payment

        trip = payment.trip
        if trip is None:
            raise ResourceNotFoundError("Associated trip not found.")

        payment.status = PaymentStatus.PROCESSING
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        try:
            self.provider.process(payment)
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            self.event_service.publish(
                OperationalEventType.PAYMENT_SUCCESS,
                ride_id=trip.ride_request_id,
                trip_id=trip.id,
                actor_id=None,
                metadata={
                    "payment_id": payment.id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status.value,
                },
            )
            self.notification_service.notify_rider(
                trip.rider.user_id,
                "PAYMENT_SUCCESS",
                {"trip_id": str(trip.id), "payment_id": str(payment.id), "status": payment.status.value},
            )
            return payment
        except Exception as exc:
            payment.status = PaymentStatus.FAILED
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            self.event_service.publish(
                OperationalEventType.PAYMENT_FAILED,
                ride_id=trip.ride_request_id,
                trip_id=trip.id,
                actor_id=None,
                metadata={
                    "payment_id": payment.id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status.value,
                },
            )
            raise RuntimeError("Mock payment processing failed.") from exc

    def calculate_fare(self, trip: Trip) -> float:
        if trip.actual_distance is None or trip.actual_duration is None:
            raise ResourceConflictError("Completed trip is missing distance or duration information.")

        amount = (
            self.settings.payment_base_fare
            + (trip.actual_distance * self.settings.payment_distance_rate_per_km)
            + (trip.actual_duration * self.settings.payment_duration_rate_per_minute)
        )
        return round(amount, 2)

    def _serialize_for_user(self, payment: Payment, current_user: User) -> PaymentResponse:
        rider_id = payment.rider_id
        amount = payment.amount
        currency = payment.currency
        payment_reference = payment.payment_reference

        if current_user.role == UserRole.SUPPORT_AGENT:
            rider_id = None
            amount = None
            currency = None
            payment_reference = None

        return PaymentResponse(
            id=payment.id,
            trip_id=payment.trip_id,
            rider_id=rider_id,
            amount=amount,
            currency=currency,
            status=payment.status,
            payment_reference=payment_reference,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    @staticmethod
    def _build_payment_reference(trip_id: UUID) -> str:
        return f"MOCK-{trip_id.hex[:12].upper()}"

    @staticmethod
    def _assert_can_access_trip(current_user: User, trip: Trip) -> None:
        if current_user.role in PAYMENT_ACCESS_ROLES:
            return
        rider = current_user.rider_profile
        if current_user.role == UserRole.RIDER and rider is not None and trip.rider_id == rider.id:
            return
        raise ResourceNotFoundError("Trip not found.")

    @staticmethod
    def _assert_can_access(current_user: User, payment: Payment) -> None:
        if current_user.role in PAYMENT_ACCESS_ROLES:
            return
        rider = current_user.rider_profile
        if current_user.role == UserRole.RIDER and rider is not None and payment.rider_id == rider.id:
            return
        raise ResourceNotFoundError("Payment not found.")

    @staticmethod
    def _assert_can_refund(current_user: User) -> None:
        if current_user.role not in PAYMENT_REFUND_ROLES:
            raise ResourceConflictError("You are not allowed to refund payments.")
