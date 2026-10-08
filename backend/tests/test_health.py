"""
Tests for health, liveness, and readiness endpoints.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root welcome endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Nutrino"
    assert "version" in data
    assert "docs" in data
    assert "health" in data


def test_health_endpoint(client: TestClient):
    """Test the comprehensive /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "development"
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["database"]["status"] == "healthy"
    assert data["database"]["database"] == "postgresql"
    assert isinstance(data["database"]["latency_ms"], (int, float))
    assert data["database"]["latency_ms"] >= 0


def test_liveness_endpoint(client: TestClient):
    """Test the /api/v1/health/live probe."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "alive"}


def test_readiness_endpoint(client: TestClient):
    """Test the /api/v1/health/ready probe."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_root_health_endpoint(client: TestClient):
    """Test top-level /health probe endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Nutrino"
    assert "version" in data

