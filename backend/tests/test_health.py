def test_health_endpoint_returns_expected_payload(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"] == "RideSphere"
    assert response.json()["database"]["status"] == "healthy"
