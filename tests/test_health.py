"""
Health check endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "checks" in data
    
    # Verify required health checks
    checks = data["checks"]
    assert "database" in checks
    assert "redis" in checks
    assert "solver" in checks
    assert "external_services" in checks


def test_liveness_check(test_client: TestClient):
    """Test the liveness check endpoint."""
    response = test_client.get("/health/liveness")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_check(test_client: TestClient):
    """Test the readiness check endpoint."""
    response = test_client.get("/health/readiness")
    
    # Should return 200 when services are ready
    # or 503 when services are not ready
    assert response.status_code in [200, 503]
    
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "ready"
        assert "critical_checks" in data


def test_metrics_endpoint(test_client: TestClient):
    """Test the metrics endpoint."""
    response = test_client.get("/health/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "version" in data
    assert "metrics" in data
    
    # Verify metrics structure
    metrics = data["metrics"]
    assert "total_requests" in metrics
    assert "active_connections" in metrics
    assert "cache_hit_rate" in metrics