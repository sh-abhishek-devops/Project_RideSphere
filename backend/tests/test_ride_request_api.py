from app.models.enums import RideRequestStatus


def _register_rider_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Ride",
                "last_name": "User",
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
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _register_driver_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Drive",
                "last_name": "User",
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


def test_rider_can_create_and_cancel_own_ride(client) -> None:
    headers = _register_rider_and_login(client, "rideowner@example.com", "RideOwner123")

    create_response = client.post(
        "/api/v1/rides",
        json={
            "pickup_address": "100 Main Street",
            "pickup_latitude": 40.71,
            "pickup_longitude": -74.0,
            "destination_address": "200 State Street",
            "destination_latitude": 40.72,
            "destination_longitude": -73.99,
            "ride_type": "STANDARD",
            "estimated_distance": 5.5,
            "estimated_duration": 14,
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == RideRequestStatus.SEARCHING_DRIVER

    ride_id = create_response.json()["id"]
    cancel_response = client.post(f"/api/v1/rides/{ride_id}/cancel", headers=headers)

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == RideRequestStatus.CANCELLED


def test_rider_only_sees_own_rides(client) -> None:
    first_headers = _register_rider_and_login(client, "rideone@example.com", "RideOne123")
    second_headers = _register_rider_and_login(client, "ridetwo@example.com", "RideTwo123")

    first_create = client.post(
        "/api/v1/rides",
        json={
            "pickup_address": "100 Main Street",
            "pickup_latitude": 40.71,
            "pickup_longitude": -74.0,
            "destination_address": "200 State Street",
            "destination_latitude": 40.72,
            "destination_longitude": -73.99,
            "ride_type": "XL",
            "estimated_distance": 8.0,
            "estimated_duration": 20,
        },
        headers=first_headers,
    )
    ride_id = first_create.json()["id"]

    own_list_response = client.get("/api/v1/rides", headers=first_headers)
    other_get_response = client.get(f"/api/v1/rides/{ride_id}", headers=second_headers)

    assert own_list_response.status_code == 200
    assert len(own_list_response.json()) == 1
    assert other_get_response.status_code == 404


def test_driver_can_list_and_accept_ride_offer(client) -> None:
    driver_one_headers = _register_driver_and_login(client, "near-driver-api@example.com", "NearDriver123")
    driver_two_headers = _register_driver_and_login(client, "far-driver-api@example.com", "FarDriver123")
    rider_headers = _register_rider_and_login(client, "rideassigned@example.com", "RideAssigned123")

    client.put(
        "/api/v1/drivers/me/availability",
        json={"status": "AVAILABLE", "latitude": 40.7129, "longitude": -74.0061},
        headers=driver_one_headers,
    )
    client.put(
        "/api/v1/drivers/me/availability",
        json={"status": "AVAILABLE", "latitude": 40.9000, "longitude": -74.3000},
        headers=driver_two_headers,
    )

    response = client.post(
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

    assert response.status_code == 201
    assert response.json()["status"] == RideRequestStatus.SEARCHING_DRIVER
    assert response.json()["driver_id"] is None

    ride_id = response.json()["id"]
    offers_response = client.get("/api/v1/drivers/me/ride-offers", headers=driver_one_headers)
    accept_response = client.post(f"/api/v1/drivers/me/ride-offers/{ride_id}/accept", headers=driver_one_headers)
    second_accept_response = client.post(f"/api/v1/drivers/me/ride-offers/{ride_id}/accept", headers=driver_two_headers)

    assert offers_response.status_code == 200
    assert offers_response.json()[0]["id"] == ride_id
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == RideRequestStatus.DRIVER_ASSIGNED
    assert accept_response.json()["driver_id"] is not None
    assert second_accept_response.status_code == 409


def test_non_rider_cannot_request_ride(client) -> None:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": "driver-ride@example.com",
                "password": "DriverRide123",
                "first_name": "Drive",
                "last_name": "User",
                "phone_number": "+15550006000",
                "is_active": True,
            }
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "driver-ride@example.com", "password": "DriverRide123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.post(
        "/api/v1/rides",
        json={
            "pickup_address": "100 Main Street",
            "pickup_latitude": 40.71,
            "pickup_longitude": -74.0,
            "destination_address": "200 State Street",
            "destination_latitude": 40.72,
            "destination_longitude": -73.99,
            "ride_type": "PREMIUM",
            "estimated_distance": 10.0,
            "estimated_duration": 22,
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_identical_pickup_and_destination_is_rejected(client) -> None:
    headers = _register_rider_and_login(client, "ridevalidation@example.com", "RideValid123")

    response = client.post(
        "/api/v1/rides",
        json={
            "pickup_address": "100 Main Street",
            "pickup_latitude": 40.71,
            "pickup_longitude": -74.0,
            "destination_address": "100 Main Street",
            "destination_latitude": 40.71,
            "destination_longitude": -74.0,
            "ride_type": "STANDARD",
            "estimated_distance": 1.0,
            "estimated_duration": 4,
        },
        headers=headers,
    )

    assert response.status_code == 422
