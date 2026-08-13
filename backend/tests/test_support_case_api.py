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
                "first_name": "Support",
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
                "first_name": "Support",
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
    driver_headers = _register_driver_and_login(client, "support-driver@example.com", "SupportDriver123")
    rider_headers = _register_rider_and_login(client, "support-rider@example.com", "SupportRider123")
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
    client.post(
        f"/api/v1/trips/{trip_id}/complete",
        json={"actual_distance": 6.1, "actual_duration": 17},
        headers=driver_headers,
    )
    return ride_response.json(), trip_id


def test_support_case_create_update_resolve_and_investigate(client, db_session) -> None:
    ride, _ = _create_completed_trip(client)
    support_headers = _create_role_user_and_login(
        client,
        db_session,
        "support-agent@example.com",
        "SupportAgent123",
        UserRole.SUPPORT_AGENT,
    )
    _create_role_user_and_login(
        client,
        db_session,
        "ops-agent@example.com",
        "OpsAgent123",
        UserRole.OPERATIONS_MANAGER,
    )

    agents_response = client.get("/api/v1/support/agents", headers=support_headers)
    case_response = client.post(
        "/api/v1/support/cases",
        json={
            "ride_request_id": ride["id"],
            "issue_summary": "Investigate delayed pickup",
            "priority": "HIGH",
        },
        headers=support_headers,
    )
    case_id = case_response.json()["id"]
    ops_agent = next(agent for agent in agents_response.json() if agent["email"] == "ops-agent@example.com")

    update_response = client.patch(
        f"/api/v1/support/cases/{case_id}",
        json={
            "assigned_agent_user_id": ops_agent["id"],
            "priority": "CRITICAL",
            "status": "INVESTIGATING",
            "resolution_notes": "Reached out to dispatch and reviewed trip status history.",
        },
        headers=support_headers,
    )
    investigation_response = client.get(
        f"/api/v1/support/cases/{case_id}/investigation",
        headers=support_headers,
    )
    resolve_response = client.post(
        f"/api/v1/support/cases/{case_id}/resolve",
        json={"resolution_notes": "Issue confirmed and rider notified."},
        headers=support_headers,
    )

    assert agents_response.status_code == 200
    assert case_response.status_code == 201
    assert case_response.json()["status"] == "OPEN"
    assert update_response.status_code == 200
    assert update_response.json()["assigned_agent_user"]["email"] == "ops-agent@example.com"
    assert update_response.json()["priority"] == "CRITICAL"
    assert update_response.json()["status"] == "INVESTIGATING"
    assert investigation_response.status_code == 200
    assert investigation_response.json()["ride_request"]["id"] == ride["id"]
    assert investigation_response.json()["trip"]["status"] == "TRIP_COMPLETED"
    assert investigation_response.json()["payment"]["status"] == "SUCCESS"
    assert investigation_response.json()["payment"]["amount"] is None
    assert investigation_response.json()["payment"]["payment_reference"] is None
    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "RESOLVED"
    assert resolve_response.json()["resolution_notes"] == "Issue confirmed and rider notified."


def test_driver_cannot_access_support_case_routes(client, db_session) -> None:
    ride, _ = _create_completed_trip(client)
    driver_headers = _register_driver_and_login(client, "blocked-driver@example.com", "BlockedDriver123")
    support_headers = _create_role_user_and_login(
        client,
        db_session,
        "support-agent-two@example.com",
        "SupportAgentTwo123",
        UserRole.SUPPORT_AGENT,
    )
    case_response = client.post(
        "/api/v1/support/cases",
        json={
            "ride_request_id": ride["id"],
            "issue_summary": "Driver should not see this case",
            "priority": "MEDIUM",
        },
        headers=support_headers,
    )

    response = client.get(f"/api/v1/support/cases/{case_response.json()['id']}", headers=driver_headers)

    assert response.status_code == 403
