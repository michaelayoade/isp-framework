"""
Unit Tests for RBAC Service

Comprehensive test suite for Role-Based Access Control service including:
- Permission checking and validation
- Row-level security and ownership
- Multi-tenant isolation
- Data filtering and access control
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.services.rbac_service import (
    RBACService, UserRole, Permission, ResourceType
)
from app.models.auth import Administrator
from app.core.exceptions import PermissionDeniedError

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

class TestRBACService:
    """Test suite for RBAC Service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rbac_service(self, mock_db):
        """RBAC service instance with mocked database."""
        return RBACService(mock_db)
    
    @pytest.fixture
    def super_admin_user(self):
        """Super admin user fixture."""
        return Administrator(
            id=1,
            username="superadmin",
            email="superadmin@example.com",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
    
    @pytest.fixture
    def admin_user(self):
        """Admin user fixture."""
        return Administrator(
            id=2,
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
    
    @pytest.fixture
    def reseller_user(self):
        """Reseller user fixture."""
        return Administrator(
            id=3,
            username="reseller",
            email="reseller@example.com",
            role=UserRole.RESELLER,
            is_active=True
        )
    
    @pytest.fixture
    def customer_user(self):
        """Customer user fixture."""
        return Administrator(
            id=4,
            username="customer",
            email="customer@example.com",
            role=UserRole.CUSTOMER,
            is_active=True
        )
    
    def test_super_admin_has_all_permissions(self, rbac_service, super_admin_user):
        """Test that super admin has all permissions."""
        # Test various permissions
        permissions_to_test = [
            Permission.CUSTOMER_CREATE,
            Permission.SERVICE_DELETE,
            Permission.BILLING_PROCESS,
            Permission.SYSTEM_CONFIG,
            Permission.NETWORK_CONFIGURE
        ]
        
        for permission in permissions_to_test:
            assert rbac_service.check_permission(super_admin_user, permission) is True
    
    def test_admin_permissions(self, rbac_service, admin_user):
        """Test admin user permissions."""
        # Admin should have these permissions
        allowed_permissions = [
            Permission.CUSTOMER_CREATE,
            Permission.CUSTOMER_READ,
            Permission.SERVICE_PROVISION,
            Permission.BILLING_READ,
            Permission.NETWORK_MANAGE
        ]
        
        for permission in allowed_permissions:
            assert rbac_service.check_permission(admin_user, permission) is True
        
        # Admin should NOT have these permissions
        denied_permissions = [
            Permission.SYSTEM_CONFIG,
            Permission.CUSTOMER_DELETE
        ]
        
        for permission in denied_permissions:
            assert rbac_service.check_permission(admin_user, permission) is False
    
    def test_reseller_permissions(self, rbac_service, reseller_user):
        """Test reseller user permissions."""
        # Reseller should have these permissions
        allowed_permissions = [
            Permission.CUSTOMER_CREATE,
            Permission.CUSTOMER_READ,
            Permission.SERVICE_CREATE,
            Permission.BILLING_READ
        ]
        
        for permission in allowed_permissions:
            assert rbac_service.check_permission(reseller_user, permission) is True
        
        # Reseller should NOT have these permissions
        denied_permissions = [
            Permission.NETWORK_MANAGE,
            Permission.SYSTEM_CONFIG,
            Permission.ADMIN_CREATE
        ]
        
        for permission in denied_permissions:
            assert rbac_service.check_permission(reseller_user, permission) is False
    
    def test_customer_permissions(self, rbac_service, customer_user):
        """Test customer user permissions."""
        # Customer should have these permissions
        allowed_permissions = [
            Permission.CUSTOMER_READ,
            Permission.SERVICE_READ,
            Permission.BILLING_READ
        ]
        
        for permission in allowed_permissions:
            assert rbac_service.check_permission(customer_user, permission) is True
        
        # Customer should NOT have these permissions
        denied_permissions = [
            Permission.CUSTOMER_CREATE,
            Permission.SERVICE_CREATE,
            Permission.BILLING_PROCESS,
            Permission.NETWORK_MANAGE
        ]
        
        for permission in denied_permissions:
            assert rbac_service.check_permission(customer_user, permission) is False
    
    def test_enforce_permission_success(self, rbac_service, admin_user):
        """Test successful permission enforcement."""
        # Should not raise exception for allowed permission
        try:
            rbac_service.enforce_permission(admin_user, Permission.CUSTOMER_READ)
        except PermissionDeniedError:
            pytest.fail("enforce_permission raised PermissionDeniedError unexpectedly")
    
    def test_enforce_permission_denied(self, rbac_service, customer_user):
        """Test permission enforcement denial."""
        # Should raise exception for denied permission
        with pytest.raises(PermissionDeniedError):
            rbac_service.enforce_permission(customer_user, Permission.CUSTOMER_CREATE)
    
    @patch.object(RBACService, '_check_resource_ownership')
    def test_resource_ownership_check(self, mock_ownership_check, rbac_service, admin_user):
        """Test resource ownership checking."""
        mock_ownership_check.return_value = True
        
        result = rbac_service.check_permission(
            admin_user, 
            Permission.CUSTOMER_READ,
            ResourceType.CUSTOMER,
            123
        )
        
        assert result is True
        mock_ownership_check.assert_called_once_with(
            admin_user, ResourceType.CUSTOMER, 123
        )
    
    @patch.object(RBACService, '_check_resource_ownership')
    def test_resource_ownership_denied(self, mock_ownership_check, rbac_service, admin_user):
        """Test resource ownership denial."""
        mock_ownership_check.return_value = False
        
        result = rbac_service.check_permission(
            admin_user, 
            Permission.CUSTOMER_READ,
            ResourceType.CUSTOMER,
            123
        )
        
        assert result is False
    
    def test_get_user_permissions_super_admin(self, rbac_service, super_admin_user):
        """Test getting all permissions for super admin."""
        permissions = rbac_service.get_user_permissions(super_admin_user)
        
        # Super admin should have all permissions
        assert len(permissions) == len(list(Permission))
        assert Permission.SYSTEM_CONFIG in permissions
        assert Permission.CUSTOMER_DELETE in permissions
    
    def test_get_user_permissions_customer(self, rbac_service, customer_user):
        """Test getting limited permissions for customer."""
        permissions = rbac_service.get_user_permissions(customer_user)
        
        # Customer should have limited permissions
        expected_permissions = [
            Permission.CUSTOMER_READ,
            Permission.SERVICE_READ,
            Permission.BILLING_READ
        ]
        
        assert len(permissions) == len(expected_permissions)
        for permission in expected_permissions:
            assert permission in permissions
    
    def test_multi_tenant_isolation_super_admin(self, rbac_service, super_admin_user):
        """Test multi-tenant isolation for super admin."""
        # Super admin can access any user's data
        assert rbac_service.check_multi_tenant_isolation(super_admin_user, 999) is True
    
    @patch.object(RBACService, '_same_organization')
    def test_multi_tenant_isolation_admin(self, mock_same_org, rbac_service, admin_user):
        """Test multi-tenant isolation for admin."""
        mock_same_org.return_value = True
        
        # Admin can access users in same organization
        assert rbac_service.check_multi_tenant_isolation(admin_user, 123) is True
        mock_same_org.assert_called_once_with(admin_user, 123)
    
    @patch.object(RBACService, '_is_reseller_customer')
    def test_multi_tenant_isolation_reseller(self, mock_is_customer, rbac_service, reseller_user):
        """Test multi-tenant isolation for reseller."""
        mock_is_customer.return_value = True
        
        # Reseller can access their customers
        assert rbac_service.check_multi_tenant_isolation(reseller_user, 456) is True
        mock_is_customer.assert_called_once_with(reseller_user.id, 456)
    
    def test_multi_tenant_isolation_customer_own_data(self, rbac_service, customer_user):
        """Test customer can access own data."""
        # Customer can access their own data
        assert rbac_service.check_multi_tenant_isolation(customer_user, customer_user.id) is True
    
    def test_multi_tenant_isolation_customer_other_data(self, rbac_service, customer_user):
        """Test customer cannot access other customer's data."""
        # Customer cannot access other customer's data
        assert rbac_service.check_multi_tenant_isolation(customer_user, 999) is False
    
    def test_validate_data_access_super_admin(self, rbac_service, super_admin_user):
        """Test data access validation for super admin."""
        test_data = {
            'id': 1,
            'name': 'Test Customer',
            'password_hash': 'secret',
            'internal_notes': 'confidential'
        }
        
        # Super admin should see all data
        result = rbac_service.validate_data_access(
            super_admin_user, test_data, ResourceType.CUSTOMER
        )
        
        assert result == test_data
    
    def test_validate_data_access_customer(self, rbac_service, customer_user):
        """Test data access validation for customer."""
        test_data = {
            'id': 1,
            'name': 'Test Customer',
            'password_hash': 'secret',
            'internal_notes': 'confidential',
            'email': 'test@example.com'
        }
        
        # Customer should not see sensitive fields
        result = rbac_service.validate_data_access(
            customer_user, test_data, ResourceType.CUSTOMER
        )
        
        assert 'password_hash' not in result
        assert 'internal_notes' not in result
        assert result['name'] == 'Test Customer'
        assert result['email'] == 'test@example.com'
    
    @patch.object(RBACService, '_get_ownership_filter')
    def test_filter_query_by_ownership(self, mock_get_filter, rbac_service, admin_user):
        """Test query filtering by ownership."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_get_filter.return_value = mock_filter
        
        result = rbac_service.filter_query_by_ownership(
            mock_query, admin_user, ResourceType.CUSTOMER
        )
        
        mock_get_filter.assert_called_once_with(admin_user, ResourceType.CUSTOMER)
        mock_query.filter.assert_called_once_with(mock_filter)
    
    def test_filter_query_by_ownership_super_admin(self, rbac_service, super_admin_user):
        """Test query filtering for super admin (no filtering)."""
        mock_query = Mock()
        
        result = rbac_service.filter_query_by_ownership(
            mock_query, super_admin_user, ResourceType.CUSTOMER
        )
        
        # Super admin query should not be filtered
        assert result == mock_query
        mock_query.filter.assert_not_called()
    
    def test_audit_access_attempt(self, rbac_service, admin_user):
        """Test access attempt auditing."""
        with patch('app.services.rbac_service.logger') as mock_logger:
            rbac_service.audit_access_attempt(
                admin_user,
                Permission.CUSTOMER_READ,
                ResourceType.CUSTOMER,
                123,
                granted=True,
                additional_context={'ip_address': '192.168.1.1'}
            )
            
            # Should log the audit record
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert 'Access audit:' in log_call
            assert admin_user.username in log_call
    
    def test_get_accessible_resources_super_admin(self, rbac_service, super_admin_user):
        """Test getting accessible resources for super admin."""
        result = rbac_service.get_accessible_resources(
            super_admin_user, ResourceType.CUSTOMER
        )
        
        # Super admin gets empty list (meaning all resources)
        assert result == []
    
    @patch.object(RBACService, '_get_owned_resource_ids')
    def test_get_accessible_resources_regular_user(self, mock_get_owned, rbac_service, admin_user):
        """Test getting accessible resources for regular user."""
        mock_get_owned.return_value = [1, 2, 3]
        
        result = rbac_service.get_accessible_resources(
            admin_user, ResourceType.CUSTOMER
        )
        
        assert result == [1, 2, 3]
        mock_get_owned.assert_called_once_with(admin_user, ResourceType.CUSTOMER)
    
    def test_permission_check_with_exception(self, rbac_service, admin_user):
        """Test permission check handles exceptions gracefully."""
        with patch.object(rbac_service, '_has_role_permission', side_effect=Exception("Test error")):
            # Should return False on exception for security
            result = rbac_service.check_permission(admin_user, Permission.CUSTOMER_READ)
            assert result is False
    
    def test_role_permissions_initialization(self, rbac_service):
        """Test that role permissions are properly initialized."""
        role_permissions = rbac_service._role_permissions
        
        # Check that all roles are defined
        assert UserRole.SUPER_ADMIN in role_permissions
        assert UserRole.ADMIN in role_permissions
        assert UserRole.RESELLER in role_permissions
        assert UserRole.CUSTOMER in role_permissions
        
        # Check that super admin has all permissions
        super_admin_perms = role_permissions[UserRole.SUPER_ADMIN]
        assert len(super_admin_perms) == len(list(Permission))
        
        # Check that customer has limited permissions
        customer_perms = role_permissions[UserRole.CUSTOMER]
        assert len(customer_perms) < len(list(Permission))
        assert Permission.CUSTOMER_READ in customer_perms
        assert Permission.SYSTEM_CONFIG not in customer_perms
    
    def test_ownership_rules_initialization(self, rbac_service):
        """Test that ownership rules are properly initialized."""
        ownership_rules = rbac_service._ownership_rules
        
        # Check that resource types are defined
        assert ResourceType.CUSTOMER in ownership_rules
        assert ResourceType.SERVICE in ownership_rules
        assert ResourceType.BILLING in ownership_rules
        
        # Check that roles have ownership fields defined
        customer_rules = ownership_rules[ResourceType.CUSTOMER]
        assert UserRole.ADMIN in customer_rules
        assert UserRole.RESELLER in customer_rules
        assert UserRole.CUSTOMER in customer_rules


# Integration tests with actual database models would go here
class TestRBACServiceIntegration:
    """Integration tests for RBAC Service with database models."""
    
    # These would be implemented when actual database models are available
    # and would test real ownership queries and filtering
    
    @pytest.mark.skip(reason="Requires database models implementation")
    def test_real_ownership_check(self):
        """Test ownership check with real database models."""
        pass
    
    @pytest.mark.skip(reason="Requires database models implementation")
    def test_real_query_filtering(self):
        """Test query filtering with real database models."""
        pass
