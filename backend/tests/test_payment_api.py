from app.models.enums import UserRole
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


def _register_rider_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Pay",
                "last_name": "Rider",
                "phone_number": f"+1555{abs(hash(email)) % 10000000:07d}",
                "is_active": True,
            }
        },
    )
    return _headers_for(client, email, password)


def _register_driver_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Pay",
                "last_name": "Driver",
                "phone_number": f"+1555{abs(hash(email)) % 10000000:07d}",
                "is_active": True,
            }
        },
    )
    return _headers_for(client, email, password)


def _create_role_user_and_login(client, db_session, email: str, password: str, role: UserRole) -> dict[str, str]:
    UserService(db_session).create_user(
        UserCreate(
            email=email,
            password=password,
            first_name="Role",
            last_name="User",
            phone_number=f"+1555{abs(hash(email)) % 10000000:07d}",
            role=role,
            is_active=True,
        )
    )
    return _headers_for(client, email, password)


def _create_completed_trip(client):
    driver_headers = _register_driver_and_login(client, "payment-api-driver@example.com", "PaymentApiDriver123")
    rider_headers = _register_rider_and_login(client, "payment-api-rider@example.com", "PaymentApiRider123")
    client.put(
        "/api/v1/drivers/me/availability",
        json={"status": "AVAILABLE", "latitude": 40.7129, "longitude": -74.0061},
        headers=driver_headers,
    )
    ride_response = client.post(
        "/api/v1/rides",
        json={
            "pickup_address": "100 Main Street",
            "pickup_latitude": 40.7128,
            "pickup_longitude": -74.0060,
            "destination_address": "200 State Street",
            "destination_latitude": 40.72,
            "destination_longitude": -73.99,
            "ride_type": "STANDARD",
            "estimated_distance": 5.5,
            "estimated_duration": 14,
        },
        headers=rider_headers,
    )
    ride_id = ride_response.json()["id"]
    accept_response = client.post(f"/api/v1/drivers/me/ride-offers/{ride_id}/accept", headers=driver_headers)
    trip_id = accept_response.json()["trip"]["id"]
    client.post(f"/api/v1/trips/{trip_id}/en-route", headers=driver_headers)
    client.post(f"/api/v1/trips/{trip_id}/arrived", headers=driver_headers)
    client.post(f"/api/v1/trips/{trip_id}/start", headers=driver_headers)
    completed = client.post(
        f"/api/v1/trips/{trip_id}/complete",
        json={"actual_distance": 6.1, "actual_duration": 17},
        headers=driver_headers,
    )
    return trip_id, rider_headers, driver_headers, completed


def test_completed_trip_exposes_payment_to_rider(client) -> None:
    trip_id, rider_headers, _, completed = _create_completed_trip(client)

    payment_response = client.get(f"/api/v1/trips/{trip_id}/payment", headers=rider_headers)

    assert completed.status_code == 200
    assert payment_response.status_code == 200
    assert payment_response.json()["status"] == "SUCCESS"
    assert payment_response.json()["amount"] == 21.12
    assert payment_response.json()["payment_reference"].startswith("MOCK-")


def test_support_agent_sees_redacted_payment_fields(client, db_session) -> None:
    trip_id, _, _, _ = _create_completed_trip(client)
    support_headers = _create_role_user_and_login(
        client,
        db_session,
        "support-api@example.com",
        "SupportApi123",
        UserRole.SUPPORT_AGENT,
    )

    response = client.get(f"/api/v1/trips/{trip_id}/payment", headers=support_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["amount"] is None
    assert response.json()["currency"] is None
    assert response.json()["payment_reference"] is None


def test_driver_cannot_access_payment_route(client) -> None:
    trip_id, _, driver_headers, _ = _create_completed_trip(client)

    response = client.get(f"/api/v1/trips/{trip_id}/payment", headers=driver_headers)

    assert response.status_code == 403


def test_payment_agent_can_refund_success_payment(client, db_session) -> None:
    trip_id, _, _, _ = _create_completed_trip(client)
    payment_agent_headers = _create_role_user_and_login(
        client,
        db_session,
        "payment-agent@example.com",
        "PaymentAgent123",
        UserRole.PAYMENT_AGENT,
    )
    payment = client.get(f"/api/v1/trips/{trip_id}/payment", headers=payment_agent_headers).json()

    refund = client.post(f"/api/v1/payments/{payment['id']}/refund", headers=payment_agent_headers)
    refund_again = client.post(f"/api/v1/payments/{payment['id']}/refund", headers=payment_agent_headers)

    assert refund.status_code == 200
    assert refund.json()["status"] == "REFUNDED"
    assert refund_again.status_code == 200
    assert refund_again.json()["status"] == "REFUNDED"
