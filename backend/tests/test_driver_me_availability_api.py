def _register_driver_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Drive",
                "last_name": "Self",
                "phone_number": f"+1555{abs(hash(email)) % 10000000:07d}",
                "is_active": True,
            }
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _register_rider_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Ride",
                "last_name": "Only",
                "phone_number": f"+1555{abs(hash(email)) % 10000000:07d}",
                "is_active": True,
            }
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_driver_can_update_and_get_own_availability(client) -> None:
    headers = _register_driver_and_login(client, "driver-self-api@example.com", "DriverSelf123")

    update_response = client.put(
        "/api/v1/drivers/me/availability",
        json={
            "status": "AVAILABLE",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        headers=headers,
    )
    get_response = client.get("/api/v1/drivers/me/availability", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "AVAILABLE"
    assert get_response.status_code == 200
    assert get_response.json()["latitude"] == 40.7128


def test_non_driver_cannot_update_driver_availability(client) -> None:
    headers = _register_rider_and_login(client, "rider-self-api@example.com", "RiderSelf123")

    response = client.put(
        "/api/v1/drivers/me/availability",
        json={
            "status": "AVAILABLE",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_driver_availability_get_creates_default_offline_record(client) -> None:
    headers = _register_driver_and_login(client, "driver-empty-api@example.com", "DriverEmpty123")

    response = client.get("/api/v1/drivers/me/availability", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "OFFLINE"
    assert response.json()["latitude"] == 0.0
    assert response.json()["longitude"] == 0.0


def test_driver_availability_rejects_invalid_coordinates(client) -> None:
    headers = _register_driver_and_login(client, "driver-invalid-api@example.com", "DriverInvalid123")

    response = client.put(
        "/api/v1/drivers/me/availability",
        json={
            "status": "AVAILABLE",
            "latitude": 120,
            "longitude": -74.0060,
        },
        headers=headers,
    )

    assert response.status_code == 422
