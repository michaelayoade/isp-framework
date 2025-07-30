from app.schemas._base import BaseSchema
from pydantic import Field
from typing import Optional, List
from datetime import datetime


# Permission schemas
class PermissionBase(BaseSchema):
    """Base schema for permissions."""
    code: str = Field(..., min_length=1, max_length=100, description="Permission code (e.g., customers.view)")
    name: str = Field(..., min_length=1, max_length=150, description="Display name")
    description: Optional[str] = Field(None, max_length=255, description="Detailed description")
    category: str = Field(..., min_length=1, max_length=50, description="Permission category")
    is_active: bool = Field(True, description="Is permission active")
    sort_order: int = Field(0, description="Sort order for UI")
    resource: str = Field(..., min_length=1, max_length=50, description="Resource (customers, invoices, etc.)")
    action: str = Field(..., min_length=1, max_length=50, description="Action (view, create, update, delete)")
    scope: str = Field("all", max_length=50, description="Scope (all, own, assigned, etc.)")
    icon_name: Optional[str] = Field(None, max_length=50, description="Icon identifier for UI")


class PermissionCreate(PermissionBase):
    """Schema for creating permission."""
    pass


class PermissionUpdate(BaseSchema):
    """Schema for updating permission."""
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    resource: Optional[str] = Field(None, min_length=1, max_length=50)
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    scope: Optional[str] = Field(None, max_length=50)
    icon_name: Optional[str] = Field(None, max_length=50)


class Permission(PermissionBase):
    """Schema for permission response."""
    id: int
    is_system: bool = Field(..., description="System permissions cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None


# Role schemas
class RoleBase(BaseSchema):
    """Base schema for roles."""
    code: str = Field(..., min_length=1, max_length=50, description="Role code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=255, description="Detailed description")
    is_active: bool = Field(True, description="Is role active")
    sort_order: int = Field(0, description="Sort order for UI")
    is_admin_role: bool = Field(False, description="Is this an administrative role")
    max_users: Optional[int] = Field(None, description="Maximum users that can have this role")
    requires_approval: bool = Field(False, description="Does assignment require approval")
    color_hex: str = Field("#6B7280", max_length=7, description="Color for role badges (#RRGGBB)")
    icon_name: Optional[str] = Field(None, max_length=50, description="Icon identifier for UI")


class RoleCreate(RoleBase):
    """Schema for creating role."""
    permission_ids: Optional[List[int]] = Field(None, description="List of permission IDs to assign")


class RoleUpdate(BaseSchema):
    """Schema for updating role."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    is_admin_role: Optional[bool] = None
    max_users: Optional[int] = None
    requires_approval: Optional[bool] = None
    color_hex: Optional[str] = Field(None, max_length=7)
    icon_name: Optional[str] = Field(None, max_length=50)


class Role(RoleBase):
    """Schema for role response."""
    id: int
    is_system: bool = Field(..., description="System roles cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: Optional[List[Permission]] = Field(None, description="Role permissions")


class RoleWithPermissions(Role):
    """Schema for role response with permissions."""
    permissions: List[Permission] = Field(..., description="Role permissions")


# User role assignment schemas
class UserRoleBase(BaseSchema):
    """Base schema for user role assignments."""
    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")
    is_active: bool = Field(True, description="Is assignment active")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class UserRoleCreate(UserRoleBase):
    """Schema for creating user role assignment."""
    pass


class UserRoleUpdate(BaseSchema):
    """Schema for updating user role assignment."""
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class UserRole(UserRoleBase):
    """Schema for user role assignment response."""
    id: int
    assigned_by: Optional[int] = Field(None, description="Who assigned this role")
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: Optional[Role] = Field(None, description="Role details")


# Permission check schemas
class PermissionCheck(BaseSchema):
    """Schema for permission check requests."""
    user_id: int = Field(..., description="User ID to check")
    permission_code: str = Field(..., description="Permission code to check")
    resource_id: Optional[int] = Field(None, description="Optional resource ID for scope checking")


class PermissionCheckResult(BaseSchema):
    """Schema for permission check results."""
    has_permission: bool = Field(..., description="Whether user has the permission")
    reason: Optional[str] = Field(None, description="Reason for denial if applicable")


# Bulk operations schemas
class BulkRolePermissionUpdate(BaseSchema):
    """Schema for bulk role permission updates."""
    role_id: int = Field(..., description="Role ID")
    permission_ids: List[int] = Field(..., description="List of permission IDs to assign")


class BulkUserRoleUpdate(BaseSchema):
    """Schema for bulk user role updates."""
    user_id: int = Field(..., description="User ID")
    role_ids: List[int] = Field(..., description="List of role IDs to assign")


# Summary schemas for dashboard/overview
class RoleSummary(BaseSchema):
    """Summary schema for role overview."""
    id: int
    name: str
    code: str
    user_count: int = Field(..., description="Number of users with this role")
    permission_count: int = Field(..., description="Number of permissions assigned")
    is_system: bool
    color_hex: str


class PermissionSummary(BaseSchema):
    """Summary schema for permission overview."""
    id: int
    name: str
    code: str
    category: str
    role_count: int = Field(..., description="Number of roles with this permission")
    is_system: bool
