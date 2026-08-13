from app.models.domain import Driver, DriverAvailability, Rider
from app.models.enums import AvailabilityStatus, PaymentStatus, RideType, TripStatus, UserRole
from app.schemas.ride_request import RideRequestCreate
from app.schemas.user import UserCreate
from app.services.payment import PaymentService
from app.services.ride_request import RideRequestService
from app.services.trip import TripService
from app.services.user import UserService


def _create_rider(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="RiderPayment123",
            first_name="Pay",
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


def _create_driver(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="DriverPayment123",
            first_name="Pay",
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
        status=AvailabilityStatus.AVAILABLE,
        latitude=40.7129,
        longitude=-74.0061,
    )
    db_session.add(availability)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_completed_trip(db_session):
    rider_user = _create_rider(db_session, "payment-rider@example.com")
    driver_user = _create_driver(db_session, "payment-driver@example.com")
    ride_request_service = RideRequestService(db_session)
    ride_request = ride_request_service.create_ride_request(
        rider_user,
        RideRequestCreate(
            pickup_address="100 Payment Street",
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            destination_address="200 Billing Avenue",
            destination_latitude=40.72,
            destination_longitude=-73.99,
            ride_type=RideType.STANDARD,
            estimated_distance=5.5,
            estimated_duration=14,
        ),
    )
    ride_request_service.accept_driver_ride_offer(ride_request.id, driver_user)
    trip_service = TripService(db_session)
    trip = trip_service.trip_repository.get_by_ride_request_id(ride_request.id)
    assert trip is not None
    trip = trip_service.mark_en_route(trip.id, driver_user)
    trip = trip_service.mark_arrived(trip.id, driver_user)
    trip = trip_service.start_trip(trip.id, driver_user)
    trip = trip_service.complete_trip(trip.id, driver_user, actual_distance=6.1, actual_duration=17)
    return trip, rider_user


def test_trip_completion_creates_successful_payment(db_session) -> None:
    trip, _ = _create_completed_trip(db_session)
    payment = PaymentService(db_session).payment_repository.get_by_trip_id(trip.id)

    assert trip.status == TripStatus.TRIP_COMPLETED
    assert payment is not None
    assert payment.status == PaymentStatus.SUCCESS
    assert payment.amount == 21.12
    assert payment.currency == "USD"


def test_payment_creation_is_idempotent_for_completed_trip(db_session) -> None:
    trip, _ = _create_completed_trip(db_session)
    service = PaymentService(db_session)

    first = service.create_payment_for_completed_trip(trip)
    second = service.create_payment_for_completed_trip(trip)

    assert first.id == second.id
    assert service.payment_repository.get_by_trip_id(trip.id) is not None


def test_support_agent_view_is_redacted(db_session) -> None:
    trip, _ = _create_completed_trip(db_session)
    support_user = UserService(db_session).create_user(
        UserCreate(
            email="support-payments@example.com",
            password="SupportPayment123",
            first_name="Support",
            last_name="Agent",
            phone_number="+15558887777",
            role=UserRole.SUPPORT_AGENT,
            is_active=True,
        )
    )

    payment = PaymentService(db_session).get_trip_payment(trip.id, support_user)

    assert payment.status == PaymentStatus.SUCCESS
    assert payment.amount is None
    assert payment.currency is None
    assert payment.payment_reference is None
