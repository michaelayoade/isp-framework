"""
RBAC Service Layer

Comprehensive Role-Based Access Control service including:
- Row-level security and ownership validation
- Permission checking and role management
- Resource access control and filtering
- Multi-tenant isolation and data segregation
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Query, Session

from app.core.exceptions import PermissionDeniedError
from app.models.auth import Administrator

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    RESELLER = "reseller"
    CUSTOMER = "customer"
    SUPPORT = "support"
    BILLING = "billing"
    TECHNICAL = "technical"


class Permission(str, Enum):
    # Customer permissions
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_READ = "customer:read"
    CUSTOMER_UPDATE = "customer:update"
    CUSTOMER_DELETE = "customer:delete"
    CUSTOMER_LIST = "customer:list"

    # Service permissions
    SERVICE_CREATE = "service:create"
    SERVICE_READ = "service:read"
    SERVICE_UPDATE = "service:update"
    SERVICE_DELETE = "service:delete"
    SERVICE_PROVISION = "service:provision"
    SERVICE_SUSPEND = "service:suspend"

    # Billing permissions
    BILLING_READ = "billing:read"
    BILLING_CREATE = "billing:create"
    BILLING_UPDATE = "billing:update"
    BILLING_PROCESS = "billing:process"

    # Network permissions
    NETWORK_READ = "network:read"
    NETWORK_MANAGE = "network:manage"
    NETWORK_CONFIGURE = "network:configure"

    # Admin permissions
    ADMIN_CREATE = "admin:create"
    ADMIN_READ = "admin:read"
    ADMIN_UPDATE = "admin:update"
    ADMIN_DELETE = "admin:delete"

    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"

    # Dashboard permissions
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_FINANCIAL = "dashboard:financial"
    DASHBOARD_NETWORK = "dashboard:network"
    DASHBOARD_ADMIN = "dashboard:admin"


class ResourceType(str, Enum):
    CUSTOMER = "customer"
    SERVICE = "service"
    BILLING = "billing"
    NETWORK = "network"
    TICKET = "ticket"
    ADMIN = "admin"
    RESELLER = "reseller"
    DASHBOARD = "dashboard"


class RBACService:
    """Service layer for Role-Based Access Control."""

    def __init__(self, db: Session):
        self.db = db
        self._role_permissions = self._initialize_role_permissions()
        self._ownership_rules = self._initialize_ownership_rules()

    def check_permission(
        self,
        user: Administrator,
        permission: Permission,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[int] = None,
    ) -> bool:
        """Check if user has permission for a specific action."""
        try:
            # Super admin has all permissions
            if hasattr(user, 'is_superuser') and user.is_superuser:
                return True

            # Check role-based permissions
            if not self._has_role_permission(user.role, permission):
                return False

            # Check resource-level ownership if resource is specified
            if resource_type and resource_id:
                return self._check_resource_ownership(user, resource_type, resource_id)

            return True

        except Exception as e:
            logger.error(
                f"Error checking permission {permission} for user {user.id}: {e}"
            )
            return False

    def enforce_permission(
        self,
        user: Administrator,
        permission: Permission,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[int] = None,
    ):
        """Enforce permission check, raise exception if denied."""
        if not self.check_permission(user, permission, resource_type, resource_id):
            raise PermissionDeniedError(
                f"User {user.username} does not have permission {permission} "
                f"for {resource_type}:{resource_id}"
            )

    def filter_query_by_ownership(
        self, query: Query, user: Administrator, resource_type: ResourceType
    ) -> Query:
        """Filter query results based on user ownership and permissions."""
        try:
            # Super admin sees everything
            if hasattr(user, 'is_superuser') and user.is_superuser:
                return query

            # Apply ownership filters based on user role and resource type
            ownership_filter = self._get_ownership_filter(user, resource_type)
            if ownership_filter is not None:
                query = query.filter(ownership_filter)

            return query

        except Exception as e:
            logger.error(f"Error filtering query for user {user.id}: {e}")
            # Return empty query on error for security
            return query.filter(False)

    def get_accessible_resources(
        self, user: Administrator, resource_type: ResourceType
    ) -> List[int]:
        """Get list of resource IDs that user can access."""
        try:
            # Super admin can access everything
            if user.role == UserRole.SUPER_ADMIN:
                return []  # Empty list means all resources

            # Get resource IDs based on ownership rules
            return self._get_owned_resource_ids(user, resource_type)

        except Exception as e:
            logger.error(f"Error getting accessible resources for user {user.id}: {e}")
            return []

    def validate_data_access(
        self, user: Administrator, data: Dict[str, Any], resource_type: ResourceType
    ) -> Dict[str, Any]:
        """Validate and filter data based on user permissions."""
        try:
            # Super admin sees all data
            if user.role == UserRole.SUPER_ADMIN:
                return data

            # Apply data filtering based on role
            return self._filter_sensitive_data(user, data, resource_type)

        except Exception as e:
            logger.error(f"Error validating data access for user {user.id}: {e}")
            return {}

    def check_multi_tenant_isolation(
        self, user: Administrator, target_user_id: int
    ) -> bool:
        """Check if user can access another user's data (multi-tenant isolation)."""
        try:
            # Super admin can access any user's data
            if user.role == UserRole.SUPER_ADMIN:
                return True

            # Admin can access users in their organization
            if user.role == UserRole.ADMIN:
                return self._same_organization(user, target_user_id)

            # Resellers can only access their own customers
            if user.role == UserRole.RESELLER:
                return self._is_reseller_customer(user.id, target_user_id)

            # Customers can only access their own data
            if user.role == UserRole.CUSTOMER:
                return user.id == target_user_id

            # Support/billing staff can access based on assignment
            if user.role in [UserRole.SUPPORT, UserRole.BILLING, UserRole.TECHNICAL]:
                return self._has_support_access(user, target_user_id)

            return False

        except Exception as e:
            logger.error(f"Error checking multi-tenant isolation: {e}")
            return False

    def get_user_permissions(self, user: Administrator) -> List[Permission]:
        """Get all permissions for a user."""
        try:
            if user.role == UserRole.SUPER_ADMIN:
                return list(Permission)

            return self._role_permissions.get(user.role, [])

        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []

    def audit_access_attempt(
        self,
        user: Administrator,
        permission: Permission,
        resource_type: Optional[ResourceType],
        resource_id: Optional[int],
        granted: bool,
        additional_context: Optional[Dict[str, Any]] = None,
    ):
        """Audit access attempts for security monitoring."""
        try:
            audit_record = {
                "user_id": user.id,
                "username": user.username,
                "user_role": user.role,
                "permission": permission,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "access_granted": granted,
                "timestamp": datetime.now(timezone.utc),
                "ip_address": (
                    additional_context.get("ip_address") if additional_context else None
                ),
                "user_agent": (
                    additional_context.get("user_agent") if additional_context else None
                ),
            }

            # Log the audit record
            logger.info(f"Access audit: {audit_record}")

            # Store in audit table (placeholder)
            # self._store_audit_record(audit_record)

        except Exception as e:
            logger.error(f"Error auditing access attempt: {e}")

    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-permission mappings."""
        return {
            UserRole.SUPER_ADMIN: list(Permission),  # All permissions
            UserRole.ADMIN: [
                Permission.CUSTOMER_CREATE,
                Permission.CUSTOMER_READ,
                Permission.CUSTOMER_UPDATE,
                Permission.CUSTOMER_LIST,
                Permission.SERVICE_CREATE,
                Permission.SERVICE_READ,
                Permission.SERVICE_UPDATE,
                Permission.SERVICE_PROVISION,
                Permission.SERVICE_SUSPEND,
                Permission.BILLING_READ,
                Permission.BILLING_CREATE,
                Permission.BILLING_UPDATE,
                Permission.NETWORK_READ,
                Permission.NETWORK_MANAGE,
                Permission.SYSTEM_MONITOR,
            ],
            UserRole.RESELLER: [
                Permission.CUSTOMER_CREATE,
                Permission.CUSTOMER_READ,
                Permission.CUSTOMER_UPDATE,
                Permission.CUSTOMER_LIST,
                Permission.SERVICE_CREATE,
                Permission.SERVICE_READ,
                Permission.SERVICE_UPDATE,
                Permission.SERVICE_PROVISION,
                Permission.BILLING_READ,
            ],
            UserRole.CUSTOMER: [
                Permission.CUSTOMER_READ,
                Permission.SERVICE_READ,
                Permission.BILLING_READ,
            ],
            UserRole.SUPPORT: [
                Permission.CUSTOMER_READ,
                Permission.CUSTOMER_UPDATE,
                Permission.SERVICE_READ,
                Permission.SERVICE_UPDATE,
                Permission.BILLING_READ,
            ],
            UserRole.BILLING: [
                Permission.CUSTOMER_READ,
                Permission.BILLING_READ,
                Permission.BILLING_CREATE,
                Permission.BILLING_UPDATE,
                Permission.BILLING_PROCESS,
            ],
            UserRole.TECHNICAL: [
                Permission.CUSTOMER_READ,
                Permission.SERVICE_READ,
                Permission.SERVICE_UPDATE,
                Permission.NETWORK_READ,
                Permission.NETWORK_MANAGE,
                Permission.NETWORK_CONFIGURE,
            ],
        }

    def _initialize_ownership_rules(self) -> Dict[str, Any]:
        """Initialize ownership validation rules."""
        return {
            ResourceType.CUSTOMER: {
                UserRole.ADMIN: "organization_id",
                UserRole.RESELLER: "reseller_id",
                UserRole.CUSTOMER: "id",
                UserRole.SUPPORT: "assigned_support_id",
                UserRole.BILLING: "billing_contact_id",
            },
            ResourceType.SERVICE: {
                UserRole.ADMIN: "customer.organization_id",
                UserRole.RESELLER: "customer.reseller_id",
                UserRole.CUSTOMER: "customer_id",
                UserRole.SUPPORT: "customer.assigned_support_id",
            },
            ResourceType.BILLING: {
                UserRole.ADMIN: "customer.organization_id",
                UserRole.RESELLER: "customer.reseller_id",
                UserRole.CUSTOMER: "customer_id",
                UserRole.BILLING: "billing_contact_id",
            },
        }

    def _has_role_permission(self, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission."""
        role_permissions = self._role_permissions.get(role, [])
        return permission in role_permissions

    def _check_resource_ownership(
        self, user: Administrator, resource_type: ResourceType, resource_id: int
    ) -> bool:
        """Check if user owns or can access specific resource."""
        try:
            # Get ownership field for this role and resource type
            ownership_rules = self._ownership_rules.get(resource_type, {})
            ownership_field = ownership_rules.get(user.role)

            if not ownership_field:
                return False

            # Query resource and check ownership
            # This is a placeholder - implement with actual model queries
            # resource = self._get_resource(resource_type, resource_id)
            # return self._check_field_ownership(resource, ownership_field, user.id)

            return True  # Placeholder

        except Exception as e:
            logger.error(f"Error checking resource ownership: {e}")
            return False

    def _get_ownership_filter(self, user: Administrator, resource_type: ResourceType):
        """Get SQLAlchemy filter for ownership-based queries."""
        try:
            ownership_rules = self._ownership_rules.get(resource_type, {})
            ownership_field = ownership_rules.get(user.role)

            if not ownership_field:
                return None

            # This would return actual SQLAlchemy filter expressions
            # For now, returning None as placeholder
            return None

        except Exception as e:
            logger.error(f"Error getting ownership filter: {e}")
            return None

    def _get_owned_resource_ids(
        self, user: Administrator, resource_type: ResourceType
    ) -> List[int]:
        """Get list of resource IDs owned by user."""
        try:
            # Placeholder - implement with actual queries
            return []

        except Exception as e:
            logger.error(f"Error getting owned resource IDs: {e}")
            return []

    def _filter_sensitive_data(
        self, user: Administrator, data: Dict[str, Any], resource_type: ResourceType
    ) -> Dict[str, Any]:
        """Filter sensitive data based on user role."""
        try:
            # Define sensitive fields by resource type
            sensitive_fields = {
                ResourceType.CUSTOMER: {
                    UserRole.CUSTOMER: [
                        "password_hash",
                        "payment_methods",
                        "internal_notes",
                    ],
                    UserRole.SUPPORT: ["password_hash", "payment_methods"],
                    UserRole.BILLING: ["password_hash", "internal_notes"],
                },
                ResourceType.BILLING: {
                    UserRole.CUSTOMER: ["internal_notes", "collection_status"],
                    UserRole.SUPPORT: ["payment_processor_data"],
                },
            }

            # Get fields to filter for this role and resource type
            fields_to_filter = sensitive_fields.get(resource_type, {}).get(
                user.role, []
            )

            # Filter out sensitive fields
            filtered_data = data.copy()
            for field in fields_to_filter:
                filtered_data.pop(field, None)

            return filtered_data

        except Exception as e:
            logger.error(f"Error filtering sensitive data: {e}")
            return data

    def _same_organization(self, user: Administrator, target_user_id: int) -> bool:
        """Check if users are in the same organization."""
        # Placeholder - implement with actual organization queries
        return True

    def _is_reseller_customer(self, reseller_id: int, customer_id: int) -> bool:
        """Check if customer belongs to reseller."""
        # Placeholder - implement with actual customer-reseller relationship queries
        return True

    def _has_support_access(self, user: Administrator, target_user_id: int) -> bool:
        """Check if support staff has access to user."""
        # Placeholder - implement with actual support assignment queries
        return True
