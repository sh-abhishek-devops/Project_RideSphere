from app.models.enums import AvailabilityStatus, UserRole
from app.schemas.user import UserCreate
from app.services.user import UserService


def _admin_headers(client, db_session) -> dict[str, str]:
    service = UserService(db_session)
    if service.get_user_by_email("admin-domain@example.com") is None:
        service.create_user(
            UserCreate(
                email="admin-domain@example.com",
                password="AdminDomain123",
                first_name="Domain",
                last_name="Admin",
                phone_number="+15550009999",
                role=UserRole.ADMIN,
                is_active=True,
            )
        )

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin-domain@example.com", "password": "AdminDomain123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_user(client, db_session) -> None:
    headers = _admin_headers(client, db_session)
    create_response = client.post(
        "/api/users",
        json={
            "email": "support@example.com",
            "password": "SupportPass123",
            "first_name": "Support",
            "last_name": "Agent",
            "phone_number": "+15550001000",
            "role": UserRole.SUPPORT_AGENT,
            "is_active": True,
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert "hashed_password" not in body
    assert body["role"] == UserRole.SUPPORT_AGENT

    get_response = client.get(f"/api/users/{body['id']}", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["email"] == "support@example.com"


def test_driver_domain_flow(client, db_session) -> None:
    headers = _admin_headers(client, db_session)
    driver_response = client.post(
        "/api/drivers",
        json={
                "user": {
                    "email": "driver@example.com",
                    "password": "DriverPass123",
                    "first_name": "Drew",
                    "last_name": "Driver",
                "phone_number": "+15550002000",
                "is_active": True,
            }
        },
        headers=headers,
    )
    assert driver_response.status_code == 201
    driver = driver_response.json()
    assert driver["user"]["role"] == UserRole.DRIVER

    vehicle_response = client.post(
        "/api/vehicles",
        json={
            "driver_id": driver["id"],
            "make": "Toyota",
            "model": "Camry",
            "year": 2024,
            "color": "Blue",
            "license_plate": "RIDE-100",
            "vehicle_type": "Sedan",
            "is_active": True,
        },
        headers=headers,
    )
    assert vehicle_response.status_code == 201
    assert vehicle_response.json()["license_plate"] == "RIDE-100"

    availability_response = client.post(
        "/api/driver-availabilities",
        json={
            "driver_id": driver["id"],
            "status": AvailabilityStatus.AVAILABLE,
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        headers=headers,
    )
    assert availability_response.status_code == 201
    assert availability_response.json()["status"] == AvailabilityStatus.AVAILABLE

    list_response = client.get("/api/drivers", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_rider_assigns_rider_role(client, db_session) -> None:
    headers = _admin_headers(client, db_session)
    response = client.post(
        "/api/riders",
        json={
                "user": {
                    "email": "rider@example.com",
                    "password": "RiderPass123",
                    "first_name": "Ria",
                    "last_name": "Rider",
                "phone_number": "+15550003000",
                "is_active": True,
            }
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["user"]["role"] == UserRole.RIDER
