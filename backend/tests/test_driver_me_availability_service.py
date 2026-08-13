import pytest

from app.models.domain import Driver
from app.models.enums import AvailabilityStatus, UserRole
from app.schemas.driver_availability import DriverSelfAvailabilityUpdate
from app.schemas.user import UserCreate
from app.services.driver_availability import DriverAvailabilityService
from app.services.exceptions import ResourceConflictError
from app.services.user import UserService


def _create_driver_user(db_session, email: str):
    user = UserService(db_session).create_user(
        UserCreate(
            email=email,
            password="DriverService123",
            first_name="Dora",
            last_name="Driver",
            phone_number="+15550007000",
            role=UserRole.DRIVER,
            is_active=True,
        )
    )
    driver = Driver(user_id=user.id)
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_driver_can_upsert_own_availability(db_session) -> None:
    user = _create_driver_user(db_session, "driver-self-service@example.com")
    service = DriverAvailabilityService(db_session)

    first = service.update_my_availability(
        user,
        DriverSelfAvailabilityUpdate(
            status=AvailabilityStatus.AVAILABLE,
            latitude=40.71,
            longitude=-74.0,
        ),
    )
    second = service.update_my_availability(
        user,
        DriverSelfAvailabilityUpdate(
            status=AvailabilityStatus.OFFLINE,
            latitude=40.72,
            longitude=-73.99,
        ),
    )

    assert first.id == second.id
    assert second.status == AvailabilityStatus.OFFLINE
    assert second.latitude == 40.72


def test_non_driver_cannot_manage_driver_availability(db_session) -> None:
    user = UserService(db_session).create_user(
        UserCreate(
            email="rider-self-service@example.com",
            password="RiderService123",
            first_name="Ria",
            last_name="Rider",
            phone_number="+15550007001",
            role=UserRole.RIDER,
            is_active=True,
        )
    )
    service = DriverAvailabilityService(db_session)

    with pytest.raises(ResourceConflictError):
        service.update_my_availability(
            user,
            DriverSelfAvailabilityUpdate(
                status=AvailabilityStatus.AVAILABLE,
                latitude=40.71,
                longitude=-74.0,
            ),
        )


def test_missing_driver_availability_creates_default_offline_record(db_session) -> None:
    user = _create_driver_user(db_session, "driver-no-availability@example.com")
    service = DriverAvailabilityService(db_session)

    availability = service.get_my_availability(user)

    assert availability.status == AvailabilityStatus.OFFLINE
    assert availability.latitude == 0.0
    assert availability.longitude == 0.0
