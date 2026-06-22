"""Integration tests for API health endpoint."""

def test_health_returns_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "version" in payload
    assert payload["services"]["api"] == "up"


def test_health_no_auth_required(client):
    response = client.get("/health", headers={})
    assert response.status_code == 200
