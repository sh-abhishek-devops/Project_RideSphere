from app.models.domain import Driver, DriverAvailability, Rider
from app.models.enums import AvailabilityStatus, RideType, UserRole
from app.repositories.operational_event import OperationalEventRecord
from app.schemas.ride_request import RideRequestCreate
from app.schemas.user import UserCreate
from app.services.operational_event import OperationalEventService, OperationalEventType
from app.services.ride_request import RideRequestService
from app.services.trip import TripService
from app.services.user import UserService


class InMemoryEventRepository:
    def __init__(self) -> None:
        self.events: list[OperationalEventRecord] = []

    def save(self, event: OperationalEventRecord) -> None:
        self.events.append(event)


class FailingEventRepository:
    def save(self, event: OperationalEventRecord) -> None:
        raise RuntimeError("mongo unavailable")


def _create_rider_user(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="RiderEvents123",
            first_name="Event",
            last_name="Rider",
            phone_number="+15550009999",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    rider = Rider(user_id=user.id)
    db_session.add(rider)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_driver_user(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="DriverEvents123",
            first_name="Event",
            last_name="Driver",
            phone_number=f"+1555{abs(hash(email)) % 10000000:07d}",
            role=UserRole.DRIVER,
            is_active=True,
        )
    )
    driver = Driver(user_id=user.id)
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
    db_session.refresh(user)
    return user


def test_operational_event_service_is_non_blocking_when_repository_fails() -> None:
    service = OperationalEventService(repository=FailingEventRepository())

    published = service.publish(
        OperationalEventType.RIDE_REQUESTED,
        metadata={"ride_type": "STANDARD"},
    )

    assert published is False


def test_ride_request_flow_emits_operational_events(db_session) -> None:
    rider_user = _create_rider_user(db_session, "event-rider@example.com")
    repository = InMemoryEventRepository()
    event_service = OperationalEventService(repository=repository)
    ride_request_service = RideRequestService(db_session, event_service=event_service)
    ride_request = ride_request_service.create_ride_request(
        rider_user,
        RideRequestCreate(
            pickup_address="100 Main Street",
            pickup_latitude=40.71,
            pickup_longitude=-74.0,
            destination_address="200 State Street",
            destination_latitude=40.72,
            destination_longitude=-73.99,
            ride_type=RideType.STANDARD,
            estimated_distance=5.5,
            estimated_duration=14,
        ),
    )

    assert ride_request.id is not None
    assert [event.event_type for event in repository.events] == [
        OperationalEventType.RIDE_REQUESTED.value,
        OperationalEventType.DRIVER_SEARCH_STARTED.value,
    ]
    assert repository.events[0].metadata == {
        "ride_type": "STANDARD",
        "estimated_distance": 5.5,
        "estimated_duration": 14,
        "status": "REQUESTED",
    }


def test_trip_completion_emits_trip_and_payment_events(db_session) -> None:
    rider_user = _create_rider_user(db_session, "event-complete-rider@example.com")
    driver_user = _create_driver_user(db_session, "event-complete-driver@example.com")
    repository = InMemoryEventRepository()
    event_service = OperationalEventService(repository=repository)

    ride_request_service = RideRequestService(db_session, event_service=event_service)
    ride_request = ride_request_service.create_ride_request(
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
    ride_request_service.accept_driver_ride_offer(ride_request.id, driver_user)
    trip = TripService(db_session, event_service=event_service).trip_repository.get_by_ride_request_id(ride_request.id)
    assert trip is not None

    trip_service = TripService(db_session, event_service=event_service)
    trip_service.mark_en_route(trip.id, driver_user)
    trip_service.mark_arrived(trip.id, driver_user)
    trip_service.start_trip(trip.id, driver_user, trip.rider_start_pin)
    trip_service.complete_trip(trip.id, driver_user, actual_distance=6.1, actual_duration=17)

    assert [event.event_type for event in repository.events] == [
        OperationalEventType.RIDE_REQUESTED.value,
        OperationalEventType.DRIVER_SEARCH_STARTED.value,
        OperationalEventType.DRIVER_ASSIGNED.value,
        OperationalEventType.DRIVER_EN_ROUTE.value,
        OperationalEventType.DRIVER_ARRIVED.value,
        OperationalEventType.TRIP_STARTED.value,
        OperationalEventType.TRIP_COMPLETED.value,
        OperationalEventType.PAYMENT_CREATED.value,
        OperationalEventType.PAYMENT_SUCCESS.value,
    ]
