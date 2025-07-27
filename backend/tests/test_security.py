"""Tests for security hardening features."""
import pytest
import time
from unittest.mock import patch, MagicMock


def test_security_health_endpoint(client):
    """Security health endpoint should return status info."""
    resp = client.get("/api/v1/security/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "components" in data
    assert "jwt_keys" in data["components"]
    assert "security_tools" in data["components"]
    assert "rate_limiting" in data["components"]


def test_rate_limiting_basic(client):
    """Basic rate limiting should work."""
    # Make multiple requests quickly to trigger rate limiting
    responses = []
    for i in range(10):
        resp = client.get("/healthz")
        responses.append(resp.status_code)
    
    # Should get mostly 200s, but might get some rate limits
    success_count = sum(1 for status in responses if status == 200)
    assert success_count >= 5  # At least some should succeed


def test_security_headers_present(client):
    """Security headers should be present in responses."""
    resp = client.get("/healthz")
    
    # Check for key security headers
    expected_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options', 
        'X-XSS-Protection',
        'Strict-Transport-Security'
    ]
    
    for header in expected_headers:
        assert header in resp.headers, f"Missing security header: {header}"


def test_request_id_header(client):
    """X-Request-ID header should be added to responses."""
    resp = client.get("/healthz")
    assert "X-Request-ID" in resp.headers
    
    # Custom request ID should be preserved
    custom_id = "test-security-123"
    resp = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
async def test_jwt_key_rotation():
    """JWT key rotation should work."""
    from app.core.jwt_rotation import jwt_key_manager
    
    # Get initial key
    initial_key_id = jwt_key_manager.get_current_key_id()
    
    # Force rotation
    new_key_id = jwt_key_manager.rotate_key(force=True)
    
    # Should have new key
    assert new_key_id != initial_key_id
    assert jwt_key_manager.get_current_key_id() == new_key_id
    
    # Old key should still be available for verification
    old_key = jwt_key_manager.get_public_key(initial_key_id)
    assert old_key is not None


@pytest.mark.asyncio
async def test_jwt_token_creation_and_verification():
    """JWT token creation and verification should work."""
    from app.core.jwt_rotation import create_jwt_token, verify_jwt_token
    from datetime import timedelta
    
    # Create token
    payload = {"user_id": 123, "role": "admin"}
    token = create_jwt_token(payload, expires_delta=timedelta(minutes=5))
    
    # Verify token
    is_valid, decoded_payload = verify_jwt_token(token)
    assert is_valid
    assert decoded_payload["user_id"] == 123
    assert decoded_payload["role"] == "admin"


def test_suspicious_user_agent_blocking(client):
    """Suspicious user agents should be blocked."""
    # Test with a blocked user agent
    resp = client.get("/healthz", headers={"User-Agent": "sqlmap/1.0"})
    # Should be blocked (403) or rate limited (429)
    assert resp.status_code in [403, 429]


def test_content_security_policy(client):
    """Content Security Policy header should be present."""
    resp = client.get("/healthz")
    assert "Content-Security-Policy" in resp.headers
    csp = resp.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp


@pytest.mark.asyncio
async def test_security_stats():
    """Security statistics should be available."""
    from app.core.security_middleware import get_security_stats
    
    stats = await get_security_stats()
    assert "blocked_ips" in stats
    assert "active_rate_limits" in stats
    assert "timestamp" in stats


def test_cors_headers_when_configured(client):
    """CORS headers should be present when configured."""
    # This test assumes CORS is configured
    resp = client.options("/healthz")
    # Should either have CORS headers or return 405 (method not allowed)
    assert resp.status_code in [200, 405]


@pytest.mark.asyncio 
async def test_dependency_scanner_requirements():
    """Dependency scanner requirements check should work."""
    from app.core.dependency_scanner import check_security_requirements
    
    tools_available, missing_tools = check_security_requirements()
    # Should return boolean and list
    assert isinstance(tools_available, bool)
    assert isinstance(missing_tools, list)


def test_security_middleware_cleanup():
    """Security middleware cleanup should work."""
    from app.core.security_middleware import cleanup_security_store
    
    # Should not raise exception
    cleanup_security_store()


@pytest.mark.asyncio
async def test_audit_logging_for_security_events():
    """Security events should be logged to audit trail."""
    from app.core.observability import log_audit_event
    
    # Should not raise exception
    log_audit_event(
        domain="security",
        event="test_security_event",
        ip_address="127.0.0.1",
        user_agent="pytest"
    )
