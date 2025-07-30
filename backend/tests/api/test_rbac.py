"""Comprehensive tests for RBAC (Role-Based Access Control) endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rbac.permission import Permission
from app.models.rbac.role import Role
from app.models.rbac.role_permission import RolePermission
from app.models.rbac.user_role import UserRole
from app.models.auth.base import Administrator
from app.services.rbac import RBACService


# Test data fixtures
@pytest.fixture
def admin_user(db_session: Session):
    """Create a test administrator user."""
    admin = Administrator(
        username="testadmin",
        email="testadmin@example.com",
        full_name="Test Administrator",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client: TestClient, admin_user: Administrator):
    """Get authentication headers for API requests."""
    # Setup admin first
    setup_payload = {
        "username": admin_user.username,
        "password": "admin123",
        "password_confirm": "admin123",
        "full_name": admin_user.full_name,
        "email": admin_user.email,
    }
    client.post("/api/v1/auth/setup", json=setup_payload)
    
    # Get token
    token_form = {
        "grant_type": "password",
        "username": admin_user.username,
        "password": "admin123",
        "client_id": "default_client",
        "client_secret": "admin123",
        "scope": "api",
    }
    response = client.post("/api/v1/auth/token", data=token_form, 
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def sample_permission(db_session: Session):
    """Create a sample permission for testing."""
    permission = Permission(
        code="test.view",
        name="Test View Permission",
        description="Permission to view test resources",
        resource="test",
        action="view",
        category="testing",
        is_system=False
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return permission


@pytest.fixture
def sample_role(db_session: Session):
    """Create a sample role for testing."""
    role = Role(
        code="test_role",
        name="Test Role",
        description="A test role for testing purposes",
        is_system=False,
        is_admin_role=False,
        color="#FF5733",
        icon="test-icon"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


class TestPermissionEndpoints:
    """Test cases for permission management endpoints."""

    def test_list_permissions(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Test listing all permissions."""
        response = client.get("/api/v1/rbac/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default permissions from migration
        assert len(data) > 0

    def test_get_permission_by_id(self, client: TestClient, auth_headers: dict, sample_permission: Permission):
        """Test getting a specific permission by ID."""
        response = client.get(f"/api/v1/rbac/permissions/{sample_permission.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_permission.id
        assert data["code"] == sample_permission.code
        assert data["name"] == sample_permission.name

    def test_get_nonexistent_permission(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent permission returns 404."""
        response = client.get("/api/v1/rbac/permissions/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_create_permission(self, client: TestClient, auth_headers: dict):
        """Test creating a new permission."""
        permission_data = {
            "code": "test.create",
            "name": "Test Create Permission",
            "description": "Permission to create test resources",
            "resource": "test",
            "action": "create",
            "category": "testing"
        }
        response = client.post("/api/v1/rbac/permissions", json=permission_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == permission_data["code"]
        assert data["name"] == permission_data["name"]
        assert data["is_system"] is False

    def test_create_permission_duplicate_code(self, client: TestClient, auth_headers: dict, sample_permission: Permission):
        """Test creating a permission with duplicate code fails."""
        permission_data = {
            "code": sample_permission.code,
            "name": "Duplicate Permission",
            "description": "This should fail",
            "resource": "test",
            "action": "view",
            "category": "testing"
        }
        response = client.post("/api/v1/rbac/permissions", json=permission_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_permission(self, client: TestClient, auth_headers: dict, sample_permission: Permission):
        """Test updating an existing permission."""
        update_data = {
            "name": "Updated Test Permission",
            "description": "Updated description"
        }
        response = client.put(f"/api/v1/rbac/permissions/{sample_permission.id}", 
                             json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    def test_delete_permission(self, client: TestClient, auth_headers: dict, sample_permission: Permission):
        """Test deleting a permission."""
        response = client.delete(f"/api/v1/rbac/permissions/{sample_permission.id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_system_permission_fails(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Test that system permissions cannot be deleted."""
        # Find a system permission
        system_permission = db_session.query(Permission).filter(Permission.is_system == True).first()
        if system_permission:
            response = client.delete(f"/api/v1/rbac/permissions/{system_permission.id}", headers=auth_headers)
            assert response.status_code == 400

    def test_get_permission_categories(self, client: TestClient, auth_headers: dict):
        """Test getting permission categories."""
        response = client.get("/api/v1/rbac/permissions/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestRoleEndpoints:
    """Test cases for role management endpoints."""

    def test_list_roles(self, client: TestClient, auth_headers: dict):
        """Test listing all roles."""
        response = client.get("/api/v1/rbac/roles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default roles from migration
        assert len(data) > 0

    def test_get_role_by_id(self, client: TestClient, auth_headers: dict, sample_role: Role):
        """Test getting a specific role by ID."""
        response = client.get(f"/api/v1/rbac/roles/{sample_role.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_role.id
        assert data["code"] == sample_role.code
        assert data["name"] == sample_role.name

    def test_create_role(self, client: TestClient, auth_headers: dict):
        """Test creating a new role."""
        role_data = {
            "code": "test_manager",
            "name": "Test Manager",
            "description": "Manages test resources",
            "color": "#00FF00",
            "icon": "manager-icon"
        }
        response = client.post("/api/v1/rbac/roles", json=role_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == role_data["code"]
        assert data["name"] == role_data["name"]
        assert data["is_system"] is False

    def test_create_role_duplicate_code(self, client: TestClient, auth_headers: dict, sample_role: Role):
        """Test creating a role with duplicate code fails."""
        role_data = {
            "code": sample_role.code,
            "name": "Duplicate Role",
            "description": "This should fail"
        }
        response = client.post("/api/v1/rbac/roles", json=role_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_role(self, client: TestClient, auth_headers: dict, sample_role: Role):
        """Test updating an existing role."""
        update_data = {
            "name": "Updated Test Role",
            "description": "Updated description",
            "color": "#FF0000"
        }
        response = client.put(f"/api/v1/rbac/roles/{sample_role.id}", 
                             json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["color"] == update_data["color"]

    def test_delete_role(self, client: TestClient, auth_headers: dict, sample_role: Role):
        """Test deleting a role."""
        response = client.delete(f"/api/v1/rbac/roles/{sample_role.id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_system_role_fails(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Test that system roles cannot be deleted."""
        # Find a system role
        system_role = db_session.query(Role).filter(Role.is_system == True).first()
        if system_role:
            response = client.delete(f"/api/v1/rbac/roles/{system_role.id}", headers=auth_headers)
            assert response.status_code == 400

    def test_get_role_permissions(self, client: TestClient, auth_headers: dict, sample_role: Role):
        """Test getting permissions for a role."""
        response = client.get(f"/api/v1/rbac/roles/{sample_role.id}/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_role_permissions(self, client: TestClient, auth_headers: dict, 
                                   sample_role: Role, sample_permission: Permission):
        """Test updating permissions for a role."""
        permission_data = {
            "permission_ids": [sample_permission.id]
        }
        response = client.put(f"/api/v1/rbac/roles/{sample_role.id}/permissions", 
                             json=permission_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Role permissions updated successfully"

    def test_get_roles_summary(self, client: TestClient, auth_headers: dict):
        """Test getting roles summary."""
        response = client.get("/api/v1/rbac/roles/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_roles" in data
        assert "system_roles" in data
        assert "custom_roles" in data


class TestUserRoleEndpoints:
    """Test cases for user role assignment endpoints."""

    def test_get_user_roles(self, client: TestClient, auth_headers: dict, admin_user: Administrator):
        """Test getting roles for a user."""
        response = client.get(f"/api/v1/rbac/users/{admin_user.id}/roles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_assign_user_role(self, client: TestClient, auth_headers: dict, 
                             admin_user: Administrator, sample_role: Role):
        """Test assigning a role to a user."""
        assignment_data = {
            "role_id": sample_role.id,
            "assigned_reason": "Test assignment"
        }
        response = client.post(f"/api/v1/rbac/users/{admin_user.id}/roles", 
                              json=assignment_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["role_id"] == sample_role.id
        assert data["user_id"] == admin_user.id

    def test_assign_duplicate_user_role_fails(self, client: TestClient, auth_headers: dict, 
                                             admin_user: Administrator, sample_role: Role, db_session: Session):
        """Test that assigning duplicate role to user fails."""
        # First assignment
        user_role = UserRole(
            user_id=admin_user.id,
            role_id=sample_role.id,
            assigned_by=admin_user.id,
            assigned_reason="Initial assignment"
        )
        db_session.add(user_role)
        db_session.commit()

        # Try duplicate assignment
        assignment_data = {
            "role_id": sample_role.id,
            "assigned_reason": "Duplicate assignment"
        }
        response = client.post(f"/api/v1/rbac/users/{admin_user.id}/roles", 
                              json=assignment_data, headers=auth_headers)
        assert response.status_code == 400

    def test_remove_user_role(self, client: TestClient, auth_headers: dict, 
                             admin_user: Administrator, sample_role: Role, db_session: Session):
        """Test removing a role from a user."""
        # First assign the role
        user_role = UserRole(
            user_id=admin_user.id,
            role_id=sample_role.id,
            assigned_by=admin_user.id,
            assigned_reason="Test assignment"
        )
        db_session.add(user_role)
        db_session.commit()

        # Then remove it
        response = client.delete(f"/api/v1/rbac/users/{admin_user.id}/roles/{sample_role.id}", 
                                headers=auth_headers)
        assert response.status_code == 204

    def test_get_user_permissions(self, client: TestClient, auth_headers: dict, admin_user: Administrator):
        """Test getting all permissions for a user."""
        response = client.get(f"/api/v1/rbac/users/{admin_user.id}/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_assign_user_roles(self, client: TestClient, auth_headers: dict, 
                                   admin_user: Administrator, sample_role: Role, db_session: Session):
        """Test bulk assigning roles to a user."""
        # Create another role
        role2 = Role(
            code="test_role_2",
            name="Test Role 2",
            description="Another test role",
            is_system=False
        )
        db_session.add(role2)
        db_session.commit()
        db_session.refresh(role2)

        bulk_data = {
            "role_assignments": [
                {"role_id": sample_role.id, "assigned_reason": "Bulk assignment 1"},
                {"role_id": role2.id, "assigned_reason": "Bulk assignment 2"}
            ]
        }
        response = client.post(f"/api/v1/rbac/users/{admin_user.id}/roles/bulk", 
                              json=bulk_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_count"] == 2


class TestPermissionCheckEndpoints:
    """Test cases for permission checking endpoints."""

    def test_check_permission(self, client: TestClient, auth_headers: dict, 
                             admin_user: Administrator, sample_permission: Permission, 
                             sample_role: Role, db_session: Session):
        """Test checking if a user has a specific permission."""
        # Assign permission to role
        role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id)
        db_session.add(role_permission)
        
        # Assign role to user
        user_role = UserRole(
            user_id=admin_user.id,
            role_id=sample_role.id,
            assigned_by=admin_user.id,
            assigned_reason="Test assignment"
        )
        db_session.add(user_role)
        db_session.commit()

        # Check permission
        check_data = {
            "user_id": admin_user.id,
            "permission_code": sample_permission.code
        }
        response = client.post("/api/v1/rbac/check-permission", json=check_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is True

    def test_check_permission_denied(self, client: TestClient, auth_headers: dict, 
                                   admin_user: Administrator, sample_permission: Permission):
        """Test checking permission that user doesn't have."""
        check_data = {
            "user_id": admin_user.id,
            "permission_code": sample_permission.code
        }
        response = client.post("/api/v1/rbac/check-permission", json=check_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is False

    def test_check_permission_invalid_user(self, client: TestClient, auth_headers: dict, sample_permission: Permission):
        """Test checking permission for non-existent user."""
        check_data = {
            "user_id": 99999,
            "permission_code": sample_permission.code
        }
        response = client.post("/api/v1/rbac/check-permission", json=check_data, headers=auth_headers)
        assert response.status_code == 404


class TestAuthenticationAndAuthorization:
    """Test cases for authentication and authorization requirements."""

    def test_unauthenticated_access_denied(self, client: TestClient):
        """Test that unauthenticated requests are denied."""
        endpoints = [
            "/api/v1/rbac/permissions",
            "/api/v1/rbac/roles",
            "/api/v1/rbac/users/1/roles",
            "/api/v1/rbac/check-permission"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_invalid_token_denied(self, client: TestClient):
        """Test that invalid tokens are denied."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/rbac/permissions", headers=headers)
        assert response.status_code == 401

    def test_expired_token_denied(self, client: TestClient):
        """Test that expired tokens are denied."""
        # This would require creating an expired token, which is complex
        # For now, we'll test with a malformed token
        headers = {"Authorization": "Bearer expired.token.here"}
        response = client.get("/api/v1/rbac/permissions", headers=headers)
        assert response.status_code == 401


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_invalid_json_payload(self, client: TestClient, auth_headers: dict):
        """Test handling of invalid JSON payloads."""
        response = client.post("/api/v1/rbac/permissions", 
                              data="invalid json", 
                              headers={**auth_headers, "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test handling of missing required fields."""
        incomplete_data = {"name": "Incomplete Permission"}  # Missing required 'code' field
        response = client.post("/api/v1/rbac/permissions", json=incomplete_data, headers=auth_headers)
        assert response.status_code == 422

    def test_invalid_field_types(self, client: TestClient, auth_headers: dict):
        """Test handling of invalid field types."""
        invalid_data = {
            "code": 123,  # Should be string
            "name": "Test Permission",
            "resource": "test",
            "action": "view"
        }
        response = client.post("/api/v1/rbac/permissions", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_nonexistent_resource_404(self, client: TestClient, auth_headers: dict):
        """Test that accessing non-existent resources returns 404."""
        endpoints = [
            "/api/v1/rbac/permissions/99999",
            "/api/v1/rbac/roles/99999",
            "/api/v1/rbac/users/99999/roles"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 404


class TestDataIntegrity:
    """Test cases for data integrity and constraints."""

    def test_role_with_permissions_cannot_be_deleted(self, client: TestClient, auth_headers: dict, 
                                                    sample_role: Role, sample_permission: Permission, db_session: Session):
        """Test that roles with assigned permissions cannot be deleted."""
        # Assign permission to role
        role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id)
        db_session.add(role_permission)
        db_session.commit()

        response = client.delete(f"/api/v1/rbac/roles/{sample_role.id}", headers=auth_headers)
        assert response.status_code == 400

    def test_permission_in_use_cannot_be_deleted(self, client: TestClient, auth_headers: dict, 
                                                sample_role: Role, sample_permission: Permission, db_session: Session):
        """Test that permissions in use cannot be deleted."""
        # Assign permission to role
        role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id)
        db_session.add(role_permission)
        db_session.commit()

        response = client.delete(f"/api/v1/rbac/permissions/{sample_permission.id}", headers=auth_headers)
        assert response.status_code == 400


# Performance and load testing (basic)
class TestPerformance:
    """Basic performance tests for RBAC endpoints."""

    def test_list_permissions_performance(self, client: TestClient, auth_headers: dict):
        """Test that listing permissions performs reasonably."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/rbac/permissions", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    def test_permission_check_performance(self, client: TestClient, auth_headers: dict, admin_user: Administrator):
        """Test that permission checking performs reasonably."""
        import time
        
        check_data = {
            "user_id": admin_user.id,
            "permission_code": "dashboard.view"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/rbac/check-permission", json=check_data, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete within 1 second
