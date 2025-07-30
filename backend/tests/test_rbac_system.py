"""Tests for RBAC (Role-Based Access Control) system."""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.rbac.models import Role, Permission, RolePermission, UserRole
from app.models.admin.base import Administrator
from app.services.rbac import RBACService
from app.core.permissions import require_permission


@pytest.mark.rbac
class TestRBACService:
    """Test RBAC service layer."""

    def test_create_permission(self, db_session: Session):
        """Test permission creation."""
        rbac_service = RBACService(db_session)
        
        permission_data = {
            "code": "test.create",
            "name": "Create Test",
            "description": "Create test resources",
            "resource": "test",
            "action": "create",
            "category": "testing"
        }
        
        permission = rbac_service.create_permission(permission_data)
        
        assert permission.code == "test.create"
        assert permission.name == "Create Test"
        assert permission.resource == "test"
        assert permission.action == "create"
        assert permission.is_active is True

    def test_create_role(self, db_session: Session):
        """Test role creation."""
        rbac_service = RBACService(db_session)
        
        role_data = {
            "code": "test_role",
            "name": "Test Role",
            "description": "Role for testing",
            "is_admin_role": False
        }
        
        role = rbac_service.create_role(role_data)
        
        assert role.code == "test_role"
        assert role.name == "Test Role"
        assert role.is_admin_role is False
        assert role.is_active is True

    def test_assign_permission_to_role(self, db_session: Session):
        """Test assigning permissions to roles."""
        rbac_service = RBACService(db_session)
        
        # Create permission
        permission = Permission(
            code="test.view",
            name="View Test",
            description="View test resources",
            resource="test",
            action="view",
            category="testing"
        )
        db_session.add(permission)
        
        # Create role
        role = Role(
            code="test_viewer",
            name="Test Viewer",
            description="Can view test resources"
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign permission to role
        rbac_service.assign_permission_to_role(role.id, permission.id)
        
        # Verify assignment
        role_permission = db_session.query(RolePermission).filter_by(
            role_id=role.id,
            permission_id=permission.id
        ).first()
        
        assert role_permission is not None

    def test_assign_role_to_user(self, db_session: Session, regular_admin):
        """Test assigning roles to users."""
        rbac_service = RBACService(db_session)
        
        # Create role
        role = Role(
            code="test_user_role",
            name="Test User Role",
            description="Role for testing user assignment"
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign role to user
        user_role = rbac_service.assign_role_to_user(regular_admin.id, role.id)
        
        assert user_role.user_id == regular_admin.id
        assert user_role.role_id == role.id
        assert user_role.is_active is True

    def test_check_user_permission(self, db_session: Session, regular_admin):
        """Test checking user permissions."""
        rbac_service = RBACService(db_session)
        
        # Create permission
        permission = Permission(
            code="test.execute",
            name="Execute Test",
            description="Execute test operations",
            resource="test",
            action="execute",
            category="testing"
        )
        db_session.add(permission)
        
        # Create role
        role = Role(
            code="test_executor",
            name="Test Executor",
            description="Can execute test operations"
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign permission to role
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id
        )
        db_session.add(role_permission)
        
        # Assign role to user
        user_role = UserRole(
            user_id=regular_admin.id,
            role_id=role.id,
            is_active=True
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Check permission
        has_permission = rbac_service.check_user_permission(regular_admin.id, "test.execute")
        assert has_permission is True
        
        # Check non-existent permission
        has_permission = rbac_service.check_user_permission(regular_admin.id, "test.nonexistent")
        assert has_permission is False

    def test_get_user_permissions(self, db_session: Session, regular_admin):
        """Test getting all user permissions."""
        rbac_service = RBACService(db_session)
        
        # Create permissions
        permissions = [
            Permission(
                code="test.read",
                name="Read Test",
                resource="test",
                action="read",
                category="testing"
            ),
            Permission(
                code="test.write",
                name="Write Test",
                resource="test",
                action="write",
                category="testing"
            )
        ]
        db_session.add_all(permissions)
        
        # Create role
        role = Role(
            code="test_readwrite",
            name="Test Read/Write",
            description="Can read and write test resources"
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign permissions to role
        for permission in permissions:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id
            )
            db_session.add(role_permission)
        
        # Assign role to user
        user_role = UserRole(
            user_id=regular_admin.id,
            role_id=role.id,
            is_active=True
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Get user permissions
        user_permissions = rbac_service.get_user_permissions(regular_admin.id)
        permission_codes = [p.code for p in user_permissions]
        
        assert "test.read" in permission_codes
        assert "test.write" in permission_codes


@pytest.mark.rbac
@pytest.mark.api
class TestRBACAPI:
    """Test RBAC API endpoints."""

    def test_get_permissions(self, client, auth_headers):
        """Test GET /api/v1/admin/rbac/permissions endpoint."""
        response = client.get("/api/v1/admin/rbac/permissions", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_permission(self, client, auth_headers):
        """Test POST /api/v1/admin/rbac/permissions endpoint."""
        permission_data = {
            "code": "api_test.create",
            "name": "API Test Create",
            "description": "Create API test resources",
            "resource": "api_test",
            "action": "create",
            "category": "testing"
        }
        
        response = client.post("/api/v1/admin/rbac/permissions", json=permission_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["code"] == "api_test.create"
        assert data["name"] == "API Test Create"

    def test_get_roles(self, client, auth_headers):
        """Test GET /api/v1/admin/rbac/roles endpoint."""
        response = client.get("/api/v1/admin/rbac/roles", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_role(self, client, auth_headers):
        """Test POST /api/v1/admin/rbac/roles endpoint."""
        role_data = {
            "code": "api_test_role",
            "name": "API Test Role",
            "description": "Role for API testing",
            "is_admin_role": False
        }
        
        response = client.post("/api/v1/admin/rbac/roles", json=role_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["code"] == "api_test_role"
        assert data["name"] == "API Test Role"

    def test_assign_permission_to_role_api(self, client, auth_headers, db_session):
        """Test POST /api/v1/admin/rbac/roles/{role_id}/permissions endpoint."""
        # Create permission and role
        permission = Permission(
            code="api_test.assign",
            name="API Test Assign",
            resource="api_test",
            action="assign",
            category="testing"
        )
        role = Role(
            code="api_test_assignee",
            name="API Test Assignee",
            description="Role for testing permission assignment"
        )
        db_session.add_all([permission, role])
        db_session.commit()
        
        assignment_data = {
            "permission_ids": [permission.id]
        }
        
        response = client.post(
            f"/api/v1/admin/rbac/roles/{role.id}/permissions",
            json=assignment_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Permissions assigned successfully"

    def test_assign_role_to_user_api(self, client, auth_headers, db_session, regular_admin):
        """Test POST /api/v1/admin/rbac/users/{user_id}/roles endpoint."""
        # Create role
        role = Role(
            code="api_test_user_role",
            name="API Test User Role",
            description="Role for testing user assignment via API"
        )
        db_session.add(role)
        db_session.commit()
        
        assignment_data = {
            "role_ids": [role.id]
        }
        
        response = client.post(
            f"/api/v1/admin/rbac/users/{regular_admin.id}/roles",
            json=assignment_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Roles assigned successfully"

    def test_get_user_permissions_api(self, client, auth_headers, super_admin):
        """Test GET /api/v1/admin/rbac/users/{user_id}/permissions endpoint."""
        response = client.get(
            f"/api/v1/admin/rbac/users/{super_admin.id}/permissions",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.rbac
@pytest.mark.integration
class TestRBACIntegration:
    """Integration tests for RBAC system."""

    def test_permission_decorator_enforcement(self, client, db_session):
        """Test that permission decorators properly enforce access control."""
        # Create a user without device permissions
        limited_admin = Administrator(
            username="limited_admin",
            email="limited@test.com",
            full_name="Limited Admin",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False
        )
        db_session.add(limited_admin)
        db_session.commit()
        
        # Create auth token for limited admin
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": limited_admin.username, "admin_id": limited_admin.id}
        )
        limited_headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access device management endpoint (should fail)
        response = client.get("/api/v1/devices", headers=limited_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_complete_rbac_workflow(self, client, auth_headers, db_session):
        """Test complete RBAC workflow from permission creation to enforcement."""
        # 1. Create custom permission
        permission_data = {
            "code": "workflow_test.manage",
            "name": "Workflow Test Manage",
            "description": "Manage workflow test resources",
            "resource": "workflow_test",
            "action": "manage",
            "category": "testing"
        }
        
        response = client.post("/api/v1/admin/rbac/permissions", json=permission_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        permission_id = response.json()["id"]

        # 2. Create custom role
        role_data = {
            "code": "workflow_manager",
            "name": "Workflow Manager",
            "description": "Can manage workflow test resources",
            "is_admin_role": True
        }
        
        response = client.post("/api/v1/admin/rbac/roles", json=role_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        role_id = response.json()["id"]

        # 3. Assign permission to role
        assignment_data = {"permission_ids": [permission_id]}
        response = client.post(
            f"/api/v1/admin/rbac/roles/{role_id}/permissions",
            json=assignment_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. Create test user
        test_admin = Administrator(
            username="workflow_test_admin",
            email="workflow@test.com",
            full_name="Workflow Test Admin",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False
        )
        db_session.add(test_admin)
        db_session.commit()

        # 5. Assign role to user
        user_assignment_data = {"role_ids": [role_id]}
        response = client.post(
            f"/api/v1/admin/rbac/users/{test_admin.id}/roles",
            json=user_assignment_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. Verify user has the permission
        response = client.get(
            f"/api/v1/admin/rbac/users/{test_admin.id}/permissions",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        permissions = response.json()
        permission_codes = [p["code"] for p in permissions]
        assert "workflow_test.manage" in permission_codes

    def test_role_hierarchy_and_inheritance(self, client, auth_headers, db_session):
        """Test role hierarchy and permission inheritance."""
        # Create base permissions
        base_permissions = [
            {
                "code": "hierarchy.read",
                "name": "Hierarchy Read",
                "resource": "hierarchy",
                "action": "read",
                "category": "testing"
            },
            {
                "code": "hierarchy.write",
                "name": "Hierarchy Write", 
                "resource": "hierarchy",
                "action": "write",
                "category": "testing"
            },
            {
                "code": "hierarchy.admin",
                "name": "Hierarchy Admin",
                "resource": "hierarchy",
                "action": "admin",
                "category": "testing"
            }
        ]
        
        created_permissions = []
        for perm_data in base_permissions:
            response = client.post("/api/v1/admin/rbac/permissions", json=perm_data, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
            created_permissions.append(response.json())

        # Create hierarchical roles
        # Reader role (basic access)
        reader_role_data = {
            "code": "hierarchy_reader",
            "name": "Hierarchy Reader",
            "description": "Can read hierarchy resources"
        }
        response = client.post("/api/v1/admin/rbac/roles", json=reader_role_data, headers=auth_headers)
        reader_role_id = response.json()["id"]
        
        # Writer role (read + write)
        writer_role_data = {
            "code": "hierarchy_writer", 
            "name": "Hierarchy Writer",
            "description": "Can read and write hierarchy resources"
        }
        response = client.post("/api/v1/admin/rbac/roles", json=writer_role_data, headers=auth_headers)
        writer_role_id = response.json()["id"]
        
        # Admin role (read + write + admin)
        admin_role_data = {
            "code": "hierarchy_admin",
            "name": "Hierarchy Admin", 
            "description": "Full hierarchy access",
            "is_admin_role": True
        }
        response = client.post("/api/v1/admin/rbac/roles", json=admin_role_data, headers=auth_headers)
        admin_role_id = response.json()["id"]

        # Assign permissions hierarchically
        # Reader gets read permission
        response = client.post(
            f"/api/v1/admin/rbac/roles/{reader_role_id}/permissions",
            json={"permission_ids": [created_permissions[0]["id"]]},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Writer gets read + write permissions
        response = client.post(
            f"/api/v1/admin/rbac/roles/{writer_role_id}/permissions",
            json={"permission_ids": [created_permissions[0]["id"], created_permissions[1]["id"]]},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Admin gets all permissions
        response = client.post(
            f"/api/v1/admin/rbac/roles/{admin_role_id}/permissions",
            json={"permission_ids": [p["id"] for p in created_permissions]},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify role permissions
        response = client.get(f"/api/v1/admin/rbac/roles/{admin_role_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        role_data = response.json()
        role_permissions = [p["code"] for p in role_data.get("permissions", [])]
        
        assert "hierarchy.read" in role_permissions
        assert "hierarchy.write" in role_permissions
        assert "hierarchy.admin" in role_permissions
