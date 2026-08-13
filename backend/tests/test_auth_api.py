from app.models.enums import UserRole
from app.schemas.user import UserCreate
from app.services.user import UserService


def _login(client, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = _login(client, email, password)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_successful_rider_registration(client) -> None:
    response = client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": "newrider@example.com",
                "password": "RiderPass123",
                "first_name": "Nina",
                "last_name": "Rider",
                "phone_number": "+15550004000",
                "is_active": True,
            }
        },
    )

    assert response.status_code == 201
    assert response.json()["rider"]["user"]["role"] == UserRole.RIDER
    assert "hashed_password" not in response.text


def test_duplicate_registration_is_rejected(client) -> None:
    payload = {
        "user": {
            "email": "duplicate@example.com",
            "password": "DuplicatePass123",
            "first_name": "Dupe",
            "last_name": "User",
            "phone_number": "+15550004001",
            "is_active": True,
        }
    }

    first = client.post("/api/v1/auth/register/rider", json=payload)
    second = client.post("/api/v1/auth/register/rider", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_returns_jwt(client) -> None:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": "driverlogin@example.com",
                "password": "DriverLogin123",
                "first_name": "Dylan",
                "last_name": "Driver",
                "phone_number": "+15550004002",
                "is_active": True,
            }
        },
    )

    response = _login(client, "driverlogin@example.com", "DriverLogin123")

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client) -> None:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": "wrongpass@example.com",
                "password": "CorrectPass123",
                "first_name": "Wendy",
                "last_name": "Wrong",
                "phone_number": "+15550004003",
                "is_active": True,
            }
        },
    )

    response = _login(client, "wrongpass@example.com", "incorrect-password")

    assert response.status_code == 401


def test_protected_route_allows_authenticated_user(client) -> None:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": "me@example.com",
                "password": "CurrentUser123",
                "first_name": "Casey",
                "last_name": "Current",
                "phone_number": "+15550004004",
                "is_active": True,
            }
        },
    )

    response = client.get("/api/v1/auth/me", headers=_auth_headers(client, "me@example.com", "CurrentUser123"))

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "me@example.com"


def test_invalid_token_is_rejected(client) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401


def test_unauthorized_role_is_rejected(client, db_session) -> None:
    service = UserService(db_session)
    service.create_user(
        UserCreate(
            email="adminauth@example.com",
            password="AdminPass123",
            first_name="Alice",
            last_name="Admin",
            phone_number="+15550004005",
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": "limited@example.com",
                "password": "LimitedPass123",
                "first_name": "Lena",
                "last_name": "Limited",
                "phone_number": "+15550004006",
                "is_active": True,
            }
        },
    )

    admin_response = client.get("/api/users", headers=_auth_headers(client, "adminauth@example.com", "AdminPass123"))
    rider_response = client.get("/api/users", headers=_auth_headers(client, "limited@example.com", "LimitedPass123"))

    assert admin_response.status_code == 200
    assert rider_response.status_code == 403
