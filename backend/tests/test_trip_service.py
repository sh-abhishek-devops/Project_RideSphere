import pytest

from app.models.domain import Driver, DriverAvailability, Rider
from app.models.enums import AvailabilityStatus, RideType, TripStatus, UserRole
from app.schemas.ride_request import RideRequestCreate
from app.schemas.user import UserCreate
from app.services.exceptions import ResourceConflictError
from app.services.ride_request import RideRequestService
from app.services.trip import TripService
from app.services.user import UserService


def _create_rider(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="RiderTrip123",
            first_name="Trip",
            last_name="Rider",
            phone_number=f"+1555{abs(hash(email)) % 10000000:07d}",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    rider = Rider(user_id=user.id)
    db_session.add(rider)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_driver(db_session, email: str, status=AvailabilityStatus.AVAILABLE):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="DriverTrip123",
            first_name="Trip",
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
    availability = DriverAvailability(
        driver_id=driver.id,
        status=status,
        latitude=40.7129,
        longitude=-74.0061,
    )
    db_session.add(availability)
    db_session.commit()
    db_session.refresh(user)
    return user, driver


def _create_assigned_trip(db_session):
    rider_user = _create_rider(db_session, "trip-rider@example.com")
    driver_user, driver = _create_driver(db_session, "trip-driver@example.com")
    ride_request_service = RideRequestService(db_session)
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
    ride_request = ride_request_service.accept_driver_ride_offer(ride_request.id, driver_user)
    trip = TripService(db_session).trip_repository.get_by_ride_request_id(ride_request.id)
    assert trip is not None
    return rider_user, driver_user, driver, ride_request, trip


def test_trip_lifecycle_and_history(db_session) -> None:
    _, driver_user, driver, _, trip = _create_assigned_trip(db_session)
    service = TripService(db_session)

    assert len(trip.rider_start_pin) == 6
    assert trip.rider_start_pin.isdigit()
    trip = service.mark_en_route(trip.id, driver_user)
    trip = service.mark_arrived(trip.id, driver_user)
    trip = service.start_trip(trip.id, driver_user, trip.rider_start_pin)
    trip = service.complete_trip(trip.id, driver_user, actual_distance=6.1, actual_duration=17)

    assert trip.status == TripStatus.TRIP_COMPLETED
    assert trip.actual_distance == 6.1
    assert trip.actual_duration == 17
    assert len(trip.status_history) == 5
    assert [item.new_status for item in trip.status_history] == [
        TripStatus.DRIVER_ASSIGNED,
        TripStatus.DRIVER_EN_ROUTE,
        TripStatus.DRIVER_ARRIVED,
        TripStatus.TRIP_STARTED,
        TripStatus.TRIP_COMPLETED,
    ]

    latest_availability = TripService(db_session).driver_availability_repository.get_latest_for_driver(driver.id)
    assert latest_availability is not None
    assert latest_availability.status == AvailabilityStatus.AVAILABLE


def test_invalid_transition_is_rejected(db_session) -> None:
    _, driver_user, _, _, trip = _create_assigned_trip(db_session)
    service = TripService(db_session)

    with pytest.raises(ResourceConflictError):
        service.start_trip(trip.id, driver_user, trip.rider_start_pin)


def test_trip_start_requires_matching_rider_pin(db_session) -> None:
    _, driver_user, _, _, trip = _create_assigned_trip(db_session)
    service = TripService(db_session)

    trip = service.mark_en_route(trip.id, driver_user)
    trip = service.mark_arrived(trip.id, driver_user)

    with pytest.raises(ResourceConflictError, match="Rider PIN does not match."):
        service.start_trip(trip.id, driver_user, "999999")


def test_only_assigned_driver_can_update_trip(db_session) -> None:
    _, _, _, _, trip = _create_assigned_trip(db_session)
    other_driver_user, _ = _create_driver(db_session, "other-trip-driver@example.com")
    service = TripService(db_session)

    with pytest.raises(ResourceConflictError):
        service.mark_en_route(trip.id, other_driver_user)


def test_driver_can_list_only_their_trips(db_session) -> None:
    _, driver_user, _, _, trip = _create_assigned_trip(db_session)
    _create_driver(db_session, "other-listing-driver@example.com")
    service = TripService(db_session)

    trips = service.list_driver_trips(driver_user)

    assert len(trips) == 1
    assert trips[0].id == trip.id
    assert trips[0].ride_request.pickup_address == "100 Main Street"
