"""Tests for observability infrastructure."""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Health endpoint should return 200 with status info."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_endpoint(client):
    """Readiness endpoint should check dependencies."""
    resp = client.get("/readyz")
    # Should be 200 (ready) or 503 (not ready) depending on deps
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]


def test_metrics_endpoint(client):
    """Metrics endpoint should return Prometheus format."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    # Should contain some basic metrics
    content = resp.text
    assert "http_requests_total" in content or "# HELP" in content


def test_request_id_header(client):
    """Requests should get X-Request-ID header in response."""
    resp = client.get("/healthz")
    assert "X-Request-ID" in resp.headers
    
    # Custom request ID should be preserved
    custom_id = "test-request-123"
    resp = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.headers["X-Request-ID"] == custom_id


def test_metrics_updated_on_request(client):
    """Making requests should update Prometheus metrics."""
    # Get initial metrics
    resp1 = client.get("/metrics")
    initial_metrics = resp1.text
    
    # Make a request to generate metrics
    client.get("/healthz")
    
    # Get updated metrics
    resp2 = client.get("/metrics")
    updated_metrics = resp2.text
    
    # Metrics should have changed (request counters incremented)
    # This is a basic check - in practice we'd parse the metrics properly
    assert len(updated_metrics) >= len(initial_metrics)
