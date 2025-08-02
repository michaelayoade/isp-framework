import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.models.rbac.permission import Permission
from app.models.rbac.role import Role
from app.models.rbac.role_permission import RolePermission
from app.models.rbac.user_role import UserRole
from app.schemas.rbac import (
    PermissionCheckResult,
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
    UserRoleCreate,
)

logger = logging.getLogger(__name__)


class RBACService:
    """Service layer for Role-Based Access Control management."""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Permission Management
    # ========================================================================

    def list_permissions(
        self, active_only: bool = True, category: Optional[str] = None
    ) -> List[Permission]:
        """List all permissions, optionally filtering by active status and category."""
        query = self.db.query(Permission)

        if active_only:
            query = query.filter(Permission.is_active is True)

        if category:
            query = query.filter(Permission.category == category)

        permissions = query.order_by(
            Permission.category, Permission.sort_order, Permission.name
        ).all()
        return permissions

    def get_permission(self, permission_id: int) -> Permission:
        """Get a permission by ID."""
        permission = (
            self.db.query(Permission).filter(Permission.id == permission_id).first()
        )
        if not permission:
            raise NotFoundError(f"Permission with ID {permission_id} not found")
        return permission

    def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Get a permission by code."""
        return self.db.query(Permission).filter(Permission.code == code).first()

    def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission."""
        # Check if code already exists
        existing = self.get_permission_by_code(permission_data.code)
        if existing:
            raise DuplicateError(
                f"Permission with code '{permission_data.code}' already exists"
            )

        # Create permission
        permission_dict = permission_data.model_dump()
        permission_dict["is_system"] = (
            False  # User-created permissions are not system permissions
        )

        permission = Permission(**permission_dict)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        logger.info(f"Created permission: {permission.code}")
        return permission

    def update_permission(
        self, permission_id: int, permission_data: PermissionUpdate
    ) -> Permission:
        """Update an existing permission."""
        permission = self.get_permission(permission_id)

        # Check if code is being changed and if it conflicts
        if permission_data.code and permission_data.code != permission.code:
            existing = self.get_permission_by_code(permission_data.code)
            if existing:
                raise DuplicateError(
                    f"Permission with code '{permission_data.code}' already exists"
                )

        # Update fields
        update_data = permission_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)

        permission.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(permission)

        logger.info(f"Updated permission {permission_id}")
        return permission

    def delete_permission(self, permission_id: int):
        """Delete a permission (only non-system permissions)."""
        permission = self.get_permission(permission_id)

        # Check if it's a system permission
        if permission.is_system:
            raise ValidationError(
                f"System permission '{permission.code}' cannot be deleted"
            )

        # Check if it's in use by roles
        roles_using_permission = (
            self.db.query(RolePermission)
            .filter(RolePermission.permission_id == permission_id)
            .count()
        )

        if roles_using_permission > 0:
            raise ValidationError(
                f"Permission '{permission.code}' is assigned to {roles_using_permission} roles and cannot be deleted"
            )

        self.db.delete(permission)
        self.db.commit()

        logger.info(f"Deleted permission {permission_id}")

    # ========================================================================
    # Role Management
    # ========================================================================

    def list_roles(
        self, active_only: bool = True, include_permissions: bool = False
    ) -> List[Role]:
        """List all roles, optionally including permissions."""
        query = self.db.query(Role)

        if active_only:
            query = query.filter(Role.is_active is True)

        if include_permissions:
            query = query.options(
                joinedload(Role.role_permissions).joinedload(RolePermission.permission)
            )

        roles = query.order_by(Role.sort_order, Role.name).all()
        return roles

    def get_role(self, role_id: int, include_permissions: bool = False) -> Role:
        """Get a role by ID."""
        query = self.db.query(Role)

        if include_permissions:
            query = query.options(
                joinedload(Role.role_permissions).joinedload(RolePermission.permission)
            )

        role = query.filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return role

    def get_role_by_code(self, code: str) -> Optional[Role]:
        """Get a role by code."""
        return self.db.query(Role).filter(Role.code == code).first()

    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        # Check if code already exists
        existing = self.get_role_by_code(role_data.code)
        if existing:
            raise DuplicateError(f"Role with code '{role_data.code}' already exists")

        # Extract permission IDs if provided
        permission_ids = role_data.permission_ids or []
        role_dict = role_data.model_dump(exclude={"permission_ids"})
        role_dict["is_system"] = False  # User-created roles are not system roles

        # Create role
        role = Role(**role_dict)
        self.db.add(role)
        self.db.flush()  # Get the role ID

        # Assign permissions if provided
        if permission_ids:
            self._assign_permissions_to_role(role.id, permission_ids)

        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Created role: {role.code}")
        return role

    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """Update an existing role."""
        role = self.get_role(role_id)

        # Check if code is being changed and if it conflicts
        if role_data.code and role_data.code != role.code:
            existing = self.get_role_by_code(role_data.code)
            if existing:
                raise DuplicateError(
                    f"Role with code '{role_data.code}' already exists"
                )

        # Update fields
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)

        role.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Updated role {role_id}")
        return role

    def delete_role(self, role_id: int):
        """Delete a role (only non-system roles)."""
        role = self.get_role(role_id)

        # Check if it's a system role
        if role.is_system:
            raise ValidationError(f"System role '{role.code}' cannot be deleted")

        # Check if it's assigned to users
        users_with_role = (
            self.db.query(UserRole)
            .filter(UserRole.role_id == role_id, UserRole.is_active is True)
            .count()
        )

        if users_with_role > 0:
            raise ValidationError(
                f"Role '{role.code}' is assigned to {users_with_role} users and cannot be deleted"
            )

        self.db.delete(role)
        self.db.commit()

        logger.info(f"Deleted role {role_id}")

    def _assign_permissions_to_role(self, role_id: int, permission_ids: List[int]):
        """Helper method to assign permissions to a role."""
        # Remove existing permissions
        self.db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

        # Add new permissions
        for permission_id in permission_ids:
            # Verify permission exists
            self.get_permission(permission_id)

            role_permission = RolePermission(
                role_id=role_id, permission_id=permission_id
            )
            self.db.add(role_permission)

    def assign_permissions_to_role(
        self, role_id: int, permission_ids: List[int]
    ) -> Role:
        """Assign permissions to a role."""
        self.get_role(role_id)
        self._assign_permissions_to_role(role_id, permission_ids)
        self.db.commit()

        logger.info(f"Assigned {len(permission_ids)} permissions to role {role_id}")
        return self.get_role(role_id, include_permissions=True)

    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Get all permissions for a role."""
        permissions = (
            self.db.query(Permission)
            .join(RolePermission)
            .filter(RolePermission.role_id == role_id, Permission.is_active is True)
            .order_by(Permission.category, Permission.sort_order)
            .all()
        )

        return permissions

    # ========================================================================
    # User Role Management
    # ========================================================================

    def assign_role_to_user(
        self, user_role_data: UserRoleCreate, assigned_by_id: int
    ) -> UserRole:
        """Assign a role to a user."""
        # Check if assignment already exists
        existing = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_role_data.user_id,
                UserRole.role_id == user_role_data.role_id,
            )
            .first()
        )

        if existing:
            if existing.is_active:
                raise DuplicateError("User already has this role assigned")
            else:
                # Reactivate existing assignment
                existing.is_active = True
                existing.assigned_by = assigned_by_id
                existing.expires_at = user_role_data.expires_at
                existing.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing)
                return existing

        # Create new assignment
        user_role_dict = user_role_data.model_dump()
        user_role_dict["assigned_by"] = assigned_by_id

        user_role = UserRole(**user_role_dict)
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)

        logger.info(
            f"Assigned role {user_role_data.role_id} to user {user_role_data.user_id}"
        )
        return user_role

    def remove_role_from_user(self, user_id: int, role_id: int):
        """Remove a role from a user."""
        user_role = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active is True,
            )
            .first()
        )

        if not user_role:
            raise NotFoundError("User role assignment not found")

        user_role.is_active = False
        user_role.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Removed role {role_id} from user {user_id}")

    def get_user_roles(self, user_id: int, active_only: bool = True) -> List[UserRole]:
        """Get all roles for a user."""
        query = (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(UserRole.user_id == user_id)
        )

        if active_only:
            query = query.filter(UserRole.is_active is True)

        # Check for expired roles
        now = datetime.now(timezone.utc)
        query = query.filter(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
        )

        return query.all()

    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user (through their roles)."""
        permissions = (
            self.db.query(Permission)
            .join(RolePermission)
            .join(Role)
            .join(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.is_active is True,
                Role.is_active is True,
                Permission.is_active is True,
                (UserRole.expires_at.is_(None))
                | (UserRole.expires_at > datetime.now(timezone.utc)),
            )
            .distinct()
            .order_by(Permission.category, Permission.sort_order)
            .all()
        )

        return permissions

    # ========================================================================
    # Permission Checking
    # ========================================================================

    def check_permission(
        self, user_id: int, permission_code: str, resource_id: Optional[int] = None
    ) -> bool:
        """Check if a user has a specific permission."""
        # Get user permissions
        user_permissions = self.get_user_permissions(user_id)

        # Check if user has the permission
        for permission in user_permissions:
            if permission.code == permission_code:
                # TODO: Implement scope checking if resource_id is provided
                # For now, just return True if permission exists
                return True

        return False

    def check_permission_detailed(
        self, user_id: int, permission_code: str, resource_id: Optional[int] = None
    ) -> PermissionCheckResult:
        """Check permission with detailed result."""
        has_permission = self.check_permission(user_id, permission_code, resource_id)

        if has_permission:
            return PermissionCheckResult(has_permission=True)
        else:
            return PermissionCheckResult(
                has_permission=False,
                reason=f"User does not have permission '{permission_code}'",
            )

    def get_user_permission_codes(self, user_id: int) -> List[str]:
        """Get all permission codes for a user."""
        permissions = self.get_user_permissions(user_id)
        return [p.code for p in permissions]

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_permission_categories(self) -> List[str]:
        """Get all permission categories."""
        categories = (
            self.db.query(Permission.category)
            .filter(Permission.is_active is True)
            .distinct()
            .order_by(Permission.category)
            .all()
        )

        return [cat[0] for cat in categories]

    def get_role_summary(self) -> List[Dict[str, Any]]:
        """Get summary information for all roles."""
        roles = self.db.query(Role).filter(Role.is_active is True).all()
        summary = []

        for role in roles:
            user_count = (
                self.db.query(UserRole)
                .filter(UserRole.role_id == role.id, UserRole.is_active is True)
                .count()
            )

            permission_count = (
                self.db.query(RolePermission)
                .filter(RolePermission.role_id == role.id)
                .count()
            )

            summary.append(
                {
                    "id": role.id,
                    "name": role.name,
                    "code": role.code,
                    "user_count": user_count,
                    "permission_count": permission_count,
                    "is_system": role.is_system,
                    "color_hex": role.color_hex,
                }
            )

        return summary

    # ========================================================================
    # User Management
    # ========================================================================

    def list_users(
        self, active_only: bool = True, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all users (administrators)."""
        from app.models import Administrator
        
        query = self.db.query(Administrator)
        
        if active_only:
            query = query.filter(Administrator.is_active is True)
        
        users = query.offset(offset).limit(limit).all()
        
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at,
                "last_login": user.last_login
            })
        
        return result
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific user by ID."""
        from app.models import Administrator
        
        user = self.db.query(Administrator).filter(Administrator.id == user_id).first()
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "permissions": user.permissions or []
        }
