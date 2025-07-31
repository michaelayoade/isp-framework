from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.rbac import RBACService
from app.schemas.rbac import (
    Permission, PermissionCreate, PermissionUpdate,
    Role, RoleCreate, RoleUpdate, RoleWithPermissions,
    UserRole, UserRoleCreate, PermissionCheck, PermissionCheckResult,
    BulkRolePermissionUpdate, RoleSummary
)
from app.api.dependencies import get_current_active_admin
from app.models import Administrator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Permission Management Endpoints
# ============================================================================

@router.get("/permissions", response_model=List[Permission])
async def list_permissions(
    active_only: bool = Query(True, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all permissions."""
    rbac_service = RBACService(db)
    
    try:
        permissions = rbac_service.list_permissions(active_only=active_only, category=category)
        return permissions
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving permissions"
        )


@router.post("/permissions", response_model=Permission, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new permission."""
    rbac_service = RBACService(db)
    
    try:
        permission = rbac_service.create_permission(permission_data)
        logger.info(f"Admin {current_admin.username} created permission: {permission.code}")
        return permission
    except Exception as e:
        logger.error(f"Error creating permission: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating permission"
        )


@router.get("/permissions/{permission_id}", response_model=Permission)
async def get_permission(
    permission_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific permission by ID."""
    rbac_service = RBACService(db)
    
    try:
        permission = rbac_service.get_permission(permission_id)
        return permission
    except Exception as e:
        logger.error(f"Error retrieving permission {permission_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving permission"
        )


@router.put("/permissions/{permission_id}", response_model=Permission)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update an existing permission."""
    rbac_service = RBACService(db)
    
    try:
        permission = rbac_service.update_permission(permission_id, permission_data)
        logger.info(f"Admin {current_admin.username} updated permission {permission_id}")
        return permission
    except Exception as e:
        logger.error(f"Error updating permission {permission_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating permission"
        )


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a permission (only non-system permissions)."""
    rbac_service = RBACService(db)
    
    try:
        rbac_service.delete_permission(permission_id)
        logger.info(f"Admin {current_admin.username} deleted permission {permission_id}")
    except Exception as e:
        logger.error(f"Error deleting permission {permission_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "system" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        elif "assigned to" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting permission"
        )


@router.get("/permissions/categories/list", response_model=List[str])
async def list_permission_categories(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all permission categories."""
    rbac_service = RBACService(db)
    
    try:
        categories = rbac_service.get_permission_categories()
        return categories
    except Exception as e:
        logger.error(f"Error listing permission categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving permission categories"
        )


# ============================================================================
# Role Management Endpoints
# ============================================================================

@router.get("/roles", response_model=List[Role])
async def list_roles(
    active_only: bool = Query(True, description="Filter by active status"),
    include_permissions: bool = Query(False, description="Include role permissions"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all roles."""
    rbac_service = RBACService(db)
    
    try:
        roles = rbac_service.list_roles(active_only=active_only, include_permissions=include_permissions)
        return roles
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving roles"
        )


@router.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new role."""
    rbac_service = RBACService(db)
    
    try:
        role = rbac_service.create_role(role_data)
        logger.info(f"Admin {current_admin.username} created role: {role.code}")
        return role
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating role"
        )


@router.get("/roles/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific role by ID with permissions."""
    rbac_service = RBACService(db)
    
    try:
        role = rbac_service.get_role(role_id, include_permissions=True)
        # Convert to response format with permissions
        permissions = rbac_service.get_role_permissions(role_id)
        role_dict = {
            **role.__dict__,
            'permissions': permissions
        }
        return role_dict
    except Exception as e:
        logger.error(f"Error retrieving role {role_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving role"
        )


@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update an existing role."""
    rbac_service = RBACService(db)
    
    try:
        role = rbac_service.update_role(role_id, role_data)
        logger.info(f"Admin {current_admin.username} updated role {role_id}")
        return role
    except Exception as e:
        logger.error(f"Error updating role {role_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating role"
        )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a role (only non-system roles)."""
    rbac_service = RBACService(db)
    
    try:
        rbac_service.delete_role(role_id)
        logger.info(f"Admin {current_admin.username} deleted role {role_id}")
    except Exception as e:
        logger.error(f"Error deleting role {role_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "system" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        elif "assigned to" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting role"
        )


@router.put("/roles/{role_id}/permissions", response_model=RoleWithPermissions)
async def assign_permissions_to_role(
    role_id: int,
    permission_update: BulkRolePermissionUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Assign permissions to a role."""
    rbac_service = RBACService(db)
    
    try:
        role = rbac_service.assign_permissions_to_role(role_id, permission_update.permission_ids)
        logger.info(f"Admin {current_admin.username} updated permissions for role {role_id}")
        
        # Return role with permissions
        permissions = rbac_service.get_role_permissions(role_id)
        role_dict = {
            **role.__dict__,
            'permissions': permissions
        }
        return role_dict
    except Exception as e:
        logger.error(f"Error assigning permissions to role {role_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assigning permissions to role"
        )


@router.get("/roles/{role_id}/permissions", response_model=List[Permission])
async def get_role_permissions(
    role_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all permissions for a role."""
    rbac_service = RBACService(db)
    
    try:
        permissions = rbac_service.get_role_permissions(role_id)
        return permissions
    except Exception as e:
        logger.error(f"Error retrieving permissions for role {role_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving role permissions"
        )


# ============================================================================
# User Role Assignment Endpoints
# ============================================================================

@router.post("/users/{user_id}/roles", response_model=UserRole, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: int,
    user_role_data: UserRoleCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Assign a role to a user."""
    rbac_service = RBACService(db)
    
    # Ensure user_id matches the URL parameter
    user_role_data.user_id = user_id
    
    try:
        user_role = rbac_service.assign_role_to_user(user_role_data, current_admin.id)
        logger.info(f"Admin {current_admin.username} assigned role {user_role_data.role_id} to user {user_id}")
        return user_role
    except Exception as e:
        logger.error(f"Error assigning role to user {user_id}: {e}")
        if "already has this role" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assigning role to user"
        )


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Remove a role from a user."""
    rbac_service = RBACService(db)
    
    try:
        rbac_service.remove_role_from_user(user_id, role_id)
        logger.info(f"Admin {current_admin.username} removed role {role_id} from user {user_id}")
    except Exception as e:
        logger.error(f"Error removing role from user {user_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing role from user"
        )


@router.get("/users/{user_id}/roles", response_model=List[UserRole])
async def get_user_roles(
    user_id: int,
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all roles for a user."""
    rbac_service = RBACService(db)
    
    try:
        user_roles = rbac_service.get_user_roles(user_id, active_only=active_only)
        return user_roles
    except Exception as e:
        logger.error(f"Error retrieving roles for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user roles"
        )


@router.get("/users/{user_id}/permissions", response_model=List[Permission])
async def get_user_permissions(
    user_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all permissions for a user (through their roles)."""
    rbac_service = RBACService(db)
    
    try:
        permissions = rbac_service.get_user_permissions(user_id)
        return permissions
    except Exception as e:
        logger.error(f"Error retrieving permissions for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user permissions"
        )


# ============================================================================
# Permission Checking Endpoints
# ============================================================================

@router.post("/check-permission", response_model=PermissionCheckResult)
async def check_permission(
    permission_check: PermissionCheck,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Check if a user has a specific permission."""
    rbac_service = RBACService(db)
    
    try:
        result = rbac_service.check_permission_detailed(
            permission_check.user_id,
            permission_check.permission_code,
            permission_check.resource_id
        )
        return result
    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking permission"
        )


@router.get("/users/{user_id}/permission-codes", response_model=List[str])
async def get_user_permission_codes(
    user_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all permission codes for a user."""
    rbac_service = RBACService(db)
    
    try:
        permission_codes = rbac_service.get_user_permission_codes(user_id)
        return permission_codes
    except Exception as e:
        logger.error(f"Error retrieving permission codes for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user permission codes"
        )


# ============================================================================
# Summary and Overview Endpoints
# ============================================================================

@router.get("/roles/summary", response_model=List[RoleSummary])
async def get_roles_summary(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get summary information for all roles."""
    rbac_service = RBACService(db)
    
    try:
        summary = rbac_service.get_role_summary()
        return summary
    except Exception as e:
        logger.error(f"Error retrieving roles summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving roles summary"
        )
