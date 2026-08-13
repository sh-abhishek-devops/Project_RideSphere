from uuid import uuid4

from app.models.domain import Driver, DriverAvailability, Rider
from app.models.enums import AvailabilityStatus, PaymentStatus, RideType, UserRole
from app.schemas.ride_request import RideRequestCreate
from app.schemas.user import UserCreate
from app.services.background_task import BackgroundTaskService
from app.services.notification import NotificationService
from app.services.operational_event import OperationalEventService
from app.services.payment import PaymentService
from app.services.ride_request import RideRequestService
from app.services.user import UserService


class TrackingEventService(OperationalEventService):
    def __init__(self) -> None:
        self.published: list[str] = []

    def publish(self, event_type, **kwargs):  # type: ignore[override]
        self.published.append(event_type.value)
        return True


class TrackingNotificationService(NotificationService):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def notify_rider(self, rider_user_id, notification_type, context):  # type: ignore[override]
        self.sent.append(("rider", notification_type))
        return True

    def notify_driver(self, driver_user_id, notification_type, context):  # type: ignore[override]
        self.sent.append(("driver", notification_type))
        return True


def _create_completed_trip(db_session):
    rider_user = UserService(db_session).create_user(
        UserCreate(
            email="bg-rider@example.com",
            password="BgRider123",
            first_name="Bg",
            last_name="Rider",
            phone_number="+15550110001",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    rider = Rider(user_id=rider_user.id)
    db_session.add(rider)
    db_session.commit()
    db_session.refresh(rider_user)

    driver_user = UserService(db_session).create_user(
        UserCreate(
            email="bg-driver@example.com",
            password="BgDriver123",
            first_name="Bg",
            last_name="Driver",
            phone_number="+15550110002",
            role=UserRole.DRIVER,
            is_active=True,
        )
    )
    driver = Driver(user_id=driver_user.id)
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(driver)
    db_session.add(
        DriverAvailability(
            driver_id=driver.id,
            status=AvailabilityStatus.AVAILABLE,
            latitude=40.7129,
            longitude=-74.0061,
        )
    )
    db_session.commit()
    db_session.refresh(driver_user)

    ride_request = RideRequestService(db_session).create_ride_request(
        rider_user,
        RideRequestCreate(
            pickup_address="100 Main Street",
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_address="200 State Street",
            destination_latitude=40.72,
            destination_longitude=-73.99,
            ride_type=RideType.STANDARD,
            estimated_distance=5.5,
            estimated_duration=14,
        ),
    )
    trip = ride_request.trip
    assert trip is not None
    trip = RideRequestService(db_session).trip_service.mark_en_route(trip.id, driver_user)
    trip = RideRequestService(db_session).trip_service.mark_arrived(trip.id, driver_user)
    trip = RideRequestService(db_session).trip_service.start_trip(trip.id, driver_user, trip.rider_start_pin)
    trip = RideRequestService(db_session).trip_service.complete_trip(
        trip.id, driver_user, actual_distance=6.1, actual_duration=17
    )
    return trip


def test_background_task_service_falls_back_inline_for_event_dispatch(monkeypatch) -> None:
    event_service = TrackingEventService()
    service = BackgroundTaskService(event_service=event_service)

    from app.tasks import operational_event_tasks

    def _fail_delay(payload):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(operational_event_tasks.process_operational_event_task, "delay", _fail_delay)

    published = service.dispatch_operational_event(
        event_type=type("EventType", (), {"value": "RIDE_REQUESTED"})(),  # type: ignore[arg-type]
        ride_id=uuid4(),
        metadata={"status": "REQUESTED"},
    )

    assert published is True
    assert event_service.published == ["RIDE_REQUESTED"]


def test_payment_processing_is_idempotent(db_session) -> None:
    trip = _create_completed_trip(db_session)
    payment_service = PaymentService(db_session)
    payment = payment_service.payment_repository.get_by_trip_id(trip.id)

    assert payment is not None
    assert payment.status == PaymentStatus.SUCCESS

    processed_again = payment_service.process_pending_payment(payment.id)

    assert processed_again.id == payment.id
    assert processed_again.status == PaymentStatus.SUCCESS
