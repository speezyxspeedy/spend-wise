"""
Tests for health check endpoint.
"""


def test_health_check_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "SpendWise" in data["app"]
    assert "version" in data
