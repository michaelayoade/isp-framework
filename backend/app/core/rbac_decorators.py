"""
RBAC Decorators and Middleware

FastAPI decorators and middleware for enforcing RBAC permissions including:
- Permission-based endpoint protection
- Row-level security enforcement
- Automatic ownership validation
- Audit logging integration
"""

from functools import wraps
from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.services.rbac_service import RBACService, Permission, ResourceType
from app.core.exceptions import PermissionDeniedError
import logging

logger = logging.getLogger(__name__)


def require_permission(
    permission: Permission,
    resource_type: Optional[ResourceType] = None,
    resource_id_param: Optional[str] = None
):
    """
    Decorator to require specific permission for endpoint access.
    
    Args:
        permission: Required permission
        resource_type: Type of resource being accessed
        resource_id_param: Name of path parameter containing resource ID
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin: Administrator = kwargs.get('current_admin')
            db: Session = kwargs.get('db')
            request: Request = kwargs.get('request')
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for RBAC check"
                )
            
            # Initialize RBAC service
            rbac_service = RBACService(db)
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Get additional context for auditing
            additional_context = {}
            if request:
                additional_context = {
                    'ip_address': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent')
                }
            
            try:
                # Check permission
                rbac_service.enforce_permission(
                    current_admin, 
                    permission, 
                    resource_type, 
                    resource_id
                )
                
                # Audit successful access
                rbac_service.audit_access_attempt(
                    current_admin,
                    permission,
                    resource_type,
                    resource_id,
                    granted=True,
                    additional_context=additional_context
                )
                
                # Call original function
                return await func(*args, **kwargs)
                
            except PermissionDeniedError as e:
                # Audit failed access attempt
                rbac_service.audit_access_attempt(
                    current_admin,
                    permission,
                    resource_type,
                    resource_id,
                    granted=False,
                    additional_context=additional_context
                )
                
                logger.warning(f"Permission denied for user {current_admin.username}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error in RBAC check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during permission check"
                )
        
        return wrapper
    return decorator


def require_ownership(
    resource_type: ResourceType,
    resource_id_param: str,
    permission: Optional[Permission] = None
):
    """
    Decorator to require resource ownership for endpoint access.
    
    Args:
        resource_type: Type of resource being accessed
        resource_id_param: Name of path parameter containing resource ID
        permission: Optional additional permission check
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin: Administrator = kwargs.get('current_admin')
            db: Session = kwargs.get('db')
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for ownership check"
                )
            
            # Get resource ID
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {resource_id_param}"
                )
            
            # Initialize RBAC service
            rbac_service = RBACService(db)
            
            try:
                # Check ownership
                if not rbac_service.check_permission(
                    current_admin, 
                    permission or Permission.CUSTOMER_READ,  # Default permission
                    resource_type, 
                    resource_id
                ):
                    raise PermissionDeniedError(
                        f"User does not have access to {resource_type} {resource_id}"
                    )
                
                # Call original function
                return await func(*args, **kwargs)
                
            except PermissionDeniedError as e:
                logger.warning(f"Ownership check failed for user {current_admin.username}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error in ownership check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during ownership check"
                )
        
        return wrapper
    return decorator


def filter_by_ownership(resource_type: ResourceType):
    """
    Decorator to automatically filter query results by ownership.
    
    Args:
        resource_type: Type of resource being queried
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin: Administrator = kwargs.get('current_admin')
            db: Session = kwargs.get('db')
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for ownership filtering"
                )
            
            # Initialize RBAC service
            rbac_service = RBACService(db)
            
            try:
                # Add RBAC service to kwargs for use in endpoint
                kwargs['rbac_service'] = rbac_service
                kwargs['resource_type'] = resource_type
                
                # Call original function
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in ownership filtering: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during ownership filtering"
                )
        
        return wrapper
    return decorator


def validate_data_access(resource_type: ResourceType):
    """
    Decorator to validate and filter response data based on user permissions.
    
    Args:
        resource_type: Type of resource in the response
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin: Administrator = kwargs.get('current_admin')
            db: Session = kwargs.get('db')
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for data validation"
                )
            
            # Initialize RBAC service
            rbac_service = RBACService(db)
            
            try:
                # Call original function
                result = await func(*args, **kwargs)
                
                # Filter response data based on permissions
                if isinstance(result, dict):
                    filtered_result = rbac_service.validate_data_access(
                        current_admin, 
                        result, 
                        resource_type
                    )
                    return filtered_result
                elif isinstance(result, list):
                    filtered_results = []
                    for item in result:
                        if isinstance(item, dict):
                            filtered_item = rbac_service.validate_data_access(
                                current_admin, 
                                item, 
                                resource_type
                            )
                            filtered_results.append(filtered_item)
                        else:
                            filtered_results.append(item)
                    return filtered_results
                else:
                    return result
                
            except Exception as e:
                logger.error(f"Error in data access validation: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during data validation"
                )
        
        return wrapper
    return decorator


def require_multi_tenant_isolation(target_user_param: str = "user_id"):
    """
    Decorator to enforce multi-tenant isolation.
    
    Args:
        target_user_param: Name of parameter containing target user ID
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_admin: Administrator = kwargs.get('current_admin')
            db: Session = kwargs.get('db')
            
            if not current_admin or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for tenant isolation check"
                )
            
            # Get target user ID
            target_user_id = kwargs.get(target_user_param)
            if not target_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {target_user_param}"
                )
            
            # Initialize RBAC service
            rbac_service = RBACService(db)
            
            try:
                # Check multi-tenant isolation
                if not rbac_service.check_multi_tenant_isolation(current_admin, target_user_id):
                    raise PermissionDeniedError(
                        f"User cannot access data for user {target_user_id}"
                    )
                
                # Call original function
                return await func(*args, **kwargs)
                
            except PermissionDeniedError as e:
                logger.warning(f"Multi-tenant isolation violation: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"Error in multi-tenant isolation check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error during tenant isolation check"
                )
        
        return wrapper
    return decorator


# Convenience decorators for common permission patterns
def admin_required(func: Callable) -> Callable:
    """Require admin role or higher."""
    return require_permission(Permission.ADMIN_READ)(func)


def customer_access_required(func: Callable) -> Callable:
    """Require customer access permission."""
    return require_permission(Permission.CUSTOMER_READ)(func)


def service_management_required(func: Callable) -> Callable:
    """Require service management permission."""
    return require_permission(Permission.SERVICE_UPDATE)(func)


def billing_access_required(func: Callable) -> Callable:
    """Require billing access permission."""
    return require_permission(Permission.BILLING_READ)(func)


def network_management_required(func: Callable) -> Callable:
    """Require network management permission."""
    return require_permission(Permission.NETWORK_MANAGE)(func)


def system_admin_required(func: Callable) -> Callable:
    """Require system administration permission."""
    return require_permission(Permission.SYSTEM_CONFIG)(func)


# Helper function to create RBAC-enabled dependencies
def get_rbac_service(db: Session = Depends(get_db)) -> RBACService:
    """Dependency to get RBAC service instance."""
    return RBACService(db)


def get_filtered_query(
    resource_type: ResourceType,
    current_admin: Administrator = Depends(get_current_admin),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Dependency to get ownership-filtered query function."""
    def filter_query(query):
        return rbac_service.filter_query_by_ownership(query, current_admin, resource_type)
    return filter_query
