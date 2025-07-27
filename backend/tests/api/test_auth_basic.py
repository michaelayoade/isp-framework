"""Basic authentication flow tests using shared TestClient fixture."""
import pytest


ADMIN_PAYLOAD = {
    "username": "admin",
    "password": "admin123",
    "password_confirm": "admin123",
    "full_name": "Test Admin",
    "email": "admin@example.com",
}

TOKEN_FORM = {
    "grant_type": "password",
    "username": ADMIN_PAYLOAD["username"],
    "password": ADMIN_PAYLOAD["password"],
    "client_id": "default_client",
    "client_secret": "admin123",
    "scope": "api",
}


@pytest.mark.order(1)
def test_admin_setup(client):
    """Initial admin setup should succeed exactly once."""
    resp = client.post("/api/v1/auth/setup", json=ADMIN_PAYLOAD)
    assert resp.status_code in (200, 400)
    # 200 on first run, 400 (already exists) on subsequent runs


@pytest.mark.order(2)
def test_password_grant_token_flow(client):
    """Password grant should return an access token for admin user."""
    resp = client.post("/api/v1/auth/token", data=TOKEN_FORM, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data and data["token_type"].lower() == "bearer"


@pytest.mark.order(3)
def test_protected_endpoint_requires_auth(client):
    """An unauthenticated request to protected endpoint should fail."""
    resp = client.get("/api/v1/customers/")
    assert resp.status_code == 401
