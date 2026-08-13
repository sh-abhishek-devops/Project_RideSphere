from datetime import UTC, date, datetime, timedelta

from app.models.domain import DriverAvailability, Payment, RideRequest, SupportCase, Trip
from app.models.enums import (
    AvailabilityStatus,
    PaymentStatus,
    RideRequestStatus,
    SupportCasePriority,
    SupportCaseStatus,
    TripStatus,
    UserRole,
)
from app.schemas.user import UserCreate
from app.services.user import UserService


def _login(client, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def _headers_for(client, email: str, password: str) -> dict[str, str]:
    response = _login(client, email, password)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_role_user_and_login(client, db_session, email: str, password: str, role: UserRole) -> dict[str, str]:
    UserService(db_session).create_user(
        UserCreate(
            email=email,
            password=password,
            first_name="Ops",
            last_name="User",
            phone_number=f"+1555{abs(hash(email)) % 10000000:07d}",
            role=role,
            is_active=True,
        )
    )
    return _headers_for(client, email, password)


def test_operations_dashboard_returns_aggregated_metrics(client, db_session) -> None:
    now = datetime.now(UTC)
    ops_headers = _create_role_user_and_login(
        client,
        db_session,
        "ops-dashboard@example.com",
        "OpsDashboard123",
        UserRole.OPERATIONS_MANAGER,
    )
    rider_user = UserService(db_session).create_user(
        UserCreate(
            email="ops-rider@example.com",
            password="OpsRider123",
            first_name="Rider",
            last_name="User",
            phone_number="+15550000001",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    driver_available_user = UserService(db_session).create_user(
        UserCreate(
            email="ops-driver-available@example.com",
            password="OpsDriverAvailable123",
            first_name="Driver",
            last_name="Available",
            phone_number="+15550000002",
            role=UserRole.DRIVER,
            is_active=True,
        )
    )
    driver_on_trip_user = UserService(db_session).create_user(
        UserCreate(
            email="ops-driver-trip@example.com",
            password="OpsDriverTrip123",
            first_name="Driver",
            last_name="Trip",
            phone_number="+15550000003",
            role=UserRole.DRIVER,
            is_active=True,
        )
    )
    support_user = UserService(db_session).create_user(
        UserCreate(
            email="ops-support@example.com",
            password="OpsSupport123",
            first_name="Support",
            last_name="Agent",
            phone_number="+15550000004",
            role=UserRole.SUPPORT_AGENT,
            is_active=True,
        )
    )

    from app.models.domain import Driver, Rider

    rider = Rider(user_id=rider_user.id)
    driver_available = Driver(user_id=driver_available_user.id)
    driver_on_trip = Driver(user_id=driver_on_trip_user.id)
    db_session.add_all([rider, driver_available, driver_on_trip])
    db_session.commit()
    db_session.refresh(rider)
    db_session.refresh(driver_available)
    db_session.refresh(driver_on_trip)

    ride_searching = RideRequest(
        rider_id=rider.id,
        driver_id=None,
        pickup_address="100 Search Street",
        pickup_latitude=40.0,
        pickup_longitude=-74.0,
        destination_address="200 Search Street",
        destination_latitude=40.1,
        destination_longitude=-73.9,
        ride_type="STANDARD",
        status=RideRequestStatus.SEARCHING_DRIVER,
        estimated_distance=5.0,
        estimated_duration=12,
    )
    ride_cancelled = RideRequest(
        rider_id=rider.id,
        driver_id=driver_available.id,
        pickup_address="100 Cancel Street",
        pickup_latitude=40.2,
        pickup_longitude=-74.2,
        destination_address="200 Cancel Street",
        destination_latitude=40.3,
        destination_longitude=-74.1,
        ride_type="STANDARD",
        status=RideRequestStatus.CANCELLED,
        estimated_distance=3.0,
        estimated_duration=9,
    )
    ride_active = RideRequest(
        rider_id=rider.id,
        driver_id=driver_on_trip.id,
        pickup_address="100 Active Street",
        pickup_latitude=40.4,
        pickup_longitude=-74.3,
        destination_address="200 Active Street",
        destination_latitude=40.5,
        destination_longitude=-74.2,
        ride_type="STANDARD",
        status=RideRequestStatus.DRIVER_ASSIGNED,
        estimated_distance=6.0,
        estimated_duration=15,
    )
    ride_completed = RideRequest(
        rider_id=rider.id,
        driver_id=driver_available.id,
        pickup_address="100 Completed Street",
        pickup_latitude=40.6,
        pickup_longitude=-74.4,
        destination_address="200 Completed Street",
        destination_latitude=40.7,
        destination_longitude=-74.3,
        ride_type="STANDARD",
        status=RideRequestStatus.DRIVER_ASSIGNED,
        estimated_distance=8.0,
        estimated_duration=20,
    )
    db_session.add_all([ride_searching, ride_cancelled, ride_active, ride_completed])
    db_session.commit()
    for ride in [ride_searching, ride_cancelled, ride_active, ride_completed]:
        ride.requested_at = now
        ride.created_at = now
        ride.updated_at = now

    active_trip = Trip(
        ride_request_id=ride_active.id,
        rider_id=rider.id,
        driver_id=driver_on_trip.id,
        vehicle_id=None,
        status=TripStatus.TRIP_STARTED,
        rider_start_pin="123456",
        started_at=now,
    )
    completed_trip = Trip(
        ride_request_id=ride_completed.id,
        rider_id=rider.id,
        driver_id=driver_available.id,
        vehicle_id=None,
        status=TripStatus.TRIP_COMPLETED,
        rider_start_pin="654321",
        started_at=now - timedelta(minutes=20),
        completed_at=now,
        actual_distance=8.1,
        actual_duration=19,
    )
    db_session.add_all([active_trip, completed_trip])
    db_session.commit()
    db_session.refresh(active_trip)
    db_session.refresh(completed_trip)
    active_trip.created_at = now
    active_trip.updated_at = now
    completed_trip.created_at = now
    completed_trip.updated_at = now

    payment_success = Payment(
        trip_id=completed_trip.id,
        rider_id=rider.id,
        amount=21.12,
        currency="USD",
        status=PaymentStatus.SUCCESS,
        payment_reference="MOCK-SUCCESS",
    )
    payment_failed = Payment(
        trip_id=active_trip.id,
        rider_id=rider.id,
        amount=18.25,
        currency="USD",
        status=PaymentStatus.FAILED,
        payment_reference="MOCK-FAILED",
    )
    db_session.add_all([payment_success, payment_failed])

    availability_available = DriverAvailability(
        driver_id=driver_available.id,
        status=AvailabilityStatus.AVAILABLE,
        latitude=40.8,
        longitude=-74.5,
    )
    availability_on_trip = DriverAvailability(
        driver_id=driver_on_trip.id,
        status=AvailabilityStatus.ON_TRIP,
        latitude=40.9,
        longitude=-74.6,
    )
    db_session.add_all([availability_available, availability_on_trip])
    db_session.commit()
    payment_success.created_at = now
    payment_success.updated_at = now
    payment_failed.created_at = now
    payment_failed.updated_at = now
    availability_available.updated_at = now
    availability_on_trip.updated_at = now

    support_case_open = SupportCase(
        ride_request_id=ride_active.id,
        trip_id=active_trip.id,
        created_by_user_id=support_user.id,
        assigned_agent_user_id=support_user.id,
        issue_summary="Active ride investigation",
        priority=SupportCasePriority.HIGH,
        status=SupportCaseStatus.INVESTIGATING,
    )
    support_case_resolved = SupportCase(
        ride_request_id=ride_completed.id,
        trip_id=completed_trip.id,
        created_by_user_id=support_user.id,
        assigned_agent_user_id=support_user.id,
        issue_summary="Completed ride closed",
        priority=SupportCasePriority.MEDIUM,
        status=SupportCaseStatus.RESOLVED,
        resolved_at=now,
    )
    db_session.add_all([support_case_open, support_case_resolved])
    db_session.commit()
    support_case_open.created_at = now
    support_case_open.updated_at = now
    support_case_resolved.created_at = now
    support_case_resolved.updated_at = now
    db_session.commit()

    response = client.get(
        f"/api/v1/operations/dashboard?date_from={date.today().isoformat()}&date_to={date.today().isoformat()}",
        headers=ops_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_ride_requests"] == 4
    assert body["rides_searching_for_drivers"] == 1
    assert body["active_trips"] == 1
    assert body["completed_trips"] == 1
    assert body["cancelled_rides"] == 1
    assert body["available_drivers"] == 1
    assert body["drivers_currently_on_trips"] == 1
    assert body["payment_successes"] == 1
    assert body["payment_failures"] == 1
    assert body["open_support_cases"] == 1


def test_operations_dashboard_rejects_unauthorized_role_and_invalid_dates(client, db_session) -> None:
    admin_headers = _create_role_user_and_login(
        client,
        db_session,
        "admin-dashboard@example.com",
        "AdminDashboard123",
        UserRole.ADMIN,
    )
    support_headers = _create_role_user_and_login(
        client,
        db_session,
        "support-dashboard@example.com",
        "SupportDashboard123",
        UserRole.SUPPORT_AGENT,
    )

    unauthorized = client.get("/api/v1/operations/dashboard", headers=support_headers)
    invalid_dates = client.get(
        "/api/v1/operations/dashboard?date_from=2026-08-11&date_to=2026-08-10",
        headers=admin_headers,
    )

    assert unauthorized.status_code == 403
    assert invalid_dates.status_code == 409
