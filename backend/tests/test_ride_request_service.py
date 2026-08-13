import pytest

from app.models.domain import Driver, DriverAvailability, Rider
from app.models.enums import RideRequestStatus, RideType, UserRole
from app.schemas.ride_request import RideRequestCreate
from app.schemas.user import UserCreate
from app.services.exceptions import ResourceConflictError
from app.services.ride_request import RideRequestService
from app.services.user import UserService


def _create_rider_user(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="RiderService123",
            first_name="Rita",
            last_name="Rider",
            phone_number="+15550005000",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    rider = Rider(user_id=user.id)
    db_session.add(rider)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_driver_with_availability(
    db_session,
    *,
    email: str,
    latitude: float,
    longitude: float,
    status,
):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="DriverService123",
            first_name="Dora",
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
        latitude=latitude,
        longitude=longitude,
    )
    db_session.add(availability)
    db_session.commit()
    return driver


def test_create_ride_request_without_drivers_moves_to_searching(db_session) -> None:
    user = _create_rider_user(db_session, "ride-service-rider@example.com")

    service = RideRequestService(db_session)
    ride_request = service.create_ride_request(
        user,
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

    assert ride_request.status == RideRequestStatus.SEARCHING_DRIVER
    assert ride_request.driver_id is None


def test_non_rider_cannot_create_ride_request(db_session) -> None:
    user = UserService(db_session).create_user(
        UserCreate(
            email="support-service@example.com",
            password="SupportService123",
            first_name="Sam",
            last_name="Support",
            phone_number="+15550005001",
            role=UserRole.SUPPORT_AGENT,
            is_active=True,
        )
    )
    service = RideRequestService(db_session)

    with pytest.raises(ResourceConflictError):
        service.create_ride_request(
            user,
            RideRequestCreate(
                pickup_address="100 Main Street",
                pickup_latitude=40.71,
                pickup_longitude=-74.0,
                destination_address="200 State Street",
                destination_latitude=40.72,
                destination_longitude=-73.99,
                ride_type=RideType.XL,
                estimated_distance=7.0,
                estimated_duration=18,
            ),
        )


def test_available_driver_sees_nearest_offer_first_and_can_accept(db_session) -> None:
    rider_user = _create_rider_user(db_session, "ride-match-rider@example.com")
    nearest_driver = _create_driver_with_availability(
        db_session,
        email="nearest-driver@example.com",
        latitude=40.7129,
        longitude=-74.0061,
        status="AVAILABLE",
    )
    _create_driver_with_availability(
        db_session,
        email="far-driver@example.com",
        latitude=40.9000,
        longitude=-74.3000,
        status="AVAILABLE",
    )

    service = RideRequestService(db_session)
    ride_request = service.create_ride_request(
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

    offers = service.list_driver_ride_offers(nearest_driver.user)
    accepted_ride = service.accept_driver_ride_offer(ride_request.id, nearest_driver.user)

    assert offers[0].id == ride_request.id
    assert accepted_ride.status == RideRequestStatus.DRIVER_ASSIGNED
    assert accepted_ride.driver_id == nearest_driver.id


def test_unavailable_and_offline_drivers_are_ignored(db_session) -> None:
    rider_user = _create_rider_user(db_session, "ride-ignore-rider@example.com")
    _create_driver_with_availability(
        db_session,
        email="reserved-driver@example.com",
        latitude=40.7127,
        longitude=-74.0059,
        status="RESERVED",
    )
    _create_driver_with_availability(
        db_session,
        email="offline-driver@example.com",
        latitude=40.7126,
        longitude=-74.0058,
        status="OFFLINE",
    )

    ride_request = RideRequestService(db_session).create_ride_request(
        rider_user,
        RideRequestCreate(
            pickup_address="100 Main Street",
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_address="200 State Street",
            destination_latitude=40.72,
            destination_longitude=-73.99,
            ride_type=RideType.XL,
            estimated_distance=7.0,
            estimated_duration=18,
        ),
    )

    assert ride_request.status == RideRequestStatus.SEARCHING_DRIVER
    assert ride_request.driver_id is None


def test_driver_cannot_receive_two_assignments(db_session) -> None:
    rider_one = _create_rider_user(db_session, "ride-rider-one@example.com")
    rider_two = _create_rider_user(db_session, "ride-rider-two@example.com")
    driver = _create_driver_with_availability(
        db_session,
        email="single-driver@example.com",
        latitude=40.7129,
        longitude=-74.0061,
        status="AVAILABLE",
    )

    service = RideRequestService(db_session)
    first_ride = service.create_ride_request(
        rider_one,
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
    second_ride = service.create_ride_request(
        rider_two,
        RideRequestCreate(
            pickup_address="300 Broad Street",
            pickup_latitude=40.7130,
            pickup_longitude=-74.0062,
            destination_address="400 Pine Street",
            destination_latitude=40.73,
            destination_longitude=-73.98,
            ride_type=RideType.PREMIUM,
            estimated_distance=8.5,
            estimated_duration=20,
        ),
    )

    accepted_first_ride = service.accept_driver_ride_offer(first_ride.id, driver.user)

    assert accepted_first_ride.status == RideRequestStatus.DRIVER_ASSIGNED
    assert accepted_first_ride.driver_id == driver.id
    assert second_ride.status == RideRequestStatus.SEARCHING_DRIVER
    assert second_ride.driver_id is None

    with pytest.raises(ResourceConflictError):
        service.accept_driver_ride_offer(second_ride.id, driver.user)
