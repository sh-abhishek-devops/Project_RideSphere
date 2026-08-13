def _register_rider_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/rider",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Trip",
                "last_name": "Rider",
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


def _register_driver_and_login(client, email: str, password: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register/driver",
        json={
            "user": {
                "email": email,
                "password": password,
                "first_name": "Trip",
                "last_name": "Driver",
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


def _create_assigned_trip(client):
    driver_headers = _register_driver_and_login(client, "trip-api-driver@example.com", "TripApiDriver123")
    rider_headers = _register_rider_and_login(client, "trip-api-rider@example.com", "TripApiRider123")
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
    client.post(f"/api/v1/drivers/me/ride-offers/{ride_id}/accept", headers=driver_headers)
    ride_response = client.get(f"/api/v1/rides/{ride_id}", headers=rider_headers)
    return driver_headers, rider_headers, ride_response


def test_trip_endpoint_progression_flow(client) -> None:
    driver_headers, rider_headers, ride_response = _create_assigned_trip(client)
    trip_id = ride_response.json()["trip"]["id"]

    get_response = client.get(f"/api/v1/trips/{trip_id}", headers=rider_headers)
    en_route = client.post(f"/api/v1/trips/{trip_id}/en-route", headers=driver_headers)
    arrived = client.post(f"/api/v1/trips/{trip_id}/arrived", headers=driver_headers)
    started = client.post(f"/api/v1/trips/{trip_id}/start", headers=driver_headers)
    completed = client.post(
        f"/api/v1/trips/{trip_id}/complete",
        json={"actual_distance": 6.1, "actual_duration": 17},
        headers=driver_headers,
    )

    assert get_response.status_code == 200
    assert en_route.status_code == 200
    assert arrived.status_code == 200
    assert started.status_code == 200
    assert completed.status_code == 200
    assert completed.json()["status"] == "TRIP_COMPLETED"
    assert len(completed.json()["status_history"]) == 5


def test_trip_invalid_transition_and_unauthorized_driver(client) -> None:
    driver_headers, rider_headers, ride_response = _create_assigned_trip(client)
    other_driver_headers = _register_driver_and_login(client, "trip-other-driver@example.com", "TripOtherDriver123")
    client.put(
        "/api/v1/drivers/me/availability",
        json={"status": "OFFLINE", "latitude": 41.0, "longitude": -74.5},
        headers=other_driver_headers,
    )
    trip_id = ride_response.json()["trip"]["id"]

    invalid = client.post(f"/api/v1/trips/{trip_id}/start", headers=driver_headers)
    unauthorized = client.post(f"/api/v1/trips/{trip_id}/en-route", headers=other_driver_headers)

    assert invalid.status_code == 409
    assert unauthorized.status_code == 409


def test_driver_can_list_own_trips_with_ride_details(client) -> None:
    driver_headers, _, ride_response = _create_assigned_trip(client)
    trip_id = ride_response.json()["trip"]["id"]

    response = client.get("/api/v1/drivers/me/trips", headers=driver_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == trip_id
    assert payload[0]["ride_request"]["pickup_address"] == "100 Main Street"
    assert payload[0]["ride_request"]["destination_address"] == "200 State Street"
