from functools import wraps
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.rbac import RBACService
from app.api.dependencies import get_current_active_admin
from app.models import Administrator
import logging

logger = logging.getLogger(__name__)


def require_permission(permission_code: str, resource_id_param: Optional[str] = None):
    """
    Decorator to require a specific permission for an endpoint.
    
    Args:
        permission_code: The permission code to check (e.g., 'customers.view')
        resource_id_param: Optional parameter name to extract resource ID from path/query params
    
    Usage:
        @require_permission('customers.view')
        async def get_customers(...):
            ...
        
        @require_permission('customers.update', 'customer_id')
        async def update_customer(customer_id: int, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, Administrator):
                    current_admin = value
                elif isinstance(value, Session):
                    db = value
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependencies not found"
                )
            
            # Extract resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission
            rbac_service = RBACService(db)
            has_permission = rbac_service.check_permission(
                current_admin.id, 
                permission_code, 
                resource_id
            )
            
            if not has_permission:
                logger.warning(f"Permission denied: User {current_admin.username} lacks '{permission_code}' permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission_code}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permission_codes: List[str]):
    """
    Decorator to require any one of multiple permissions for an endpoint.
    
    Args:
        permission_codes: List of permission codes, user needs at least one
    
    Usage:
        @require_any_permission(['customers.view', 'customers.update'])
        async def get_customer_details(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, Administrator):
                    current_admin = value
                elif isinstance(value, Session):
                    db = value
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependencies not found"
                )
            
            # Check if user has any of the required permissions
            rbac_service = RBACService(db)
            has_any_permission = False
            
            for permission_code in permission_codes:
                if rbac_service.check_permission(current_admin.id, permission_code):
                    has_any_permission = True
                    break
            
            if not has_any_permission:
                logger.warning(f"Permission denied: User {current_admin.username} lacks any of {permission_codes} permissions")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required one of: {', '.join(permission_codes)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin_role():
    """
    Decorator to require an administrative role for an endpoint.
    
    Usage:
        @require_admin_role()
        async def manage_system_settings(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, Administrator):
                    current_admin = value
                elif isinstance(value, Session):
                    db = value
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependencies not found"
                )
            
            # Check if user has any admin role
            rbac_service = RBACService(db)
            user_roles = rbac_service.get_user_roles(current_admin.id)
            
            has_admin_role = any(role.role.is_admin_role for role in user_roles)
            
            if not has_admin_role:
                logger.warning(f"Admin role required: User {current_admin.username} lacks administrative role")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrative role required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class PermissionChecker:
    """
    Utility class for checking permissions in service layers or other contexts.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rbac_service = RBACService(db)
    
    def check_permission(self, user_id: int, permission_code: str, resource_id: Optional[int] = None) -> bool:
        """Check if a user has a specific permission."""
        return self.rbac_service.check_permission(user_id, permission_code, resource_id)
    
    def check_any_permission(self, user_id: int, permission_codes: List[str]) -> bool:
        """Check if a user has any of the specified permissions."""
        return any(
            self.rbac_service.check_permission(user_id, code) 
            for code in permission_codes
        )
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permission codes for a user."""
        return self.rbac_service.get_user_permission_codes(user_id)
    
    def has_admin_role(self, user_id: int) -> bool:
        """Check if user has any administrative role."""
        user_roles = self.rbac_service.get_user_roles(user_id)
        return any(role.role.is_admin_role for role in user_roles)


# Convenience functions for common permission checks
async def get_permission_checker(db: Session = Depends(get_db)) -> PermissionChecker:
    """Dependency to get a PermissionChecker instance."""
    return PermissionChecker(db)


async def get_current_user_permissions(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
) -> List[str]:
    """Dependency to get current user's permission codes."""
    rbac_service = RBACService(db)
    return rbac_service.get_user_permission_codes(current_admin.id)
