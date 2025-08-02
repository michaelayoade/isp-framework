import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, ValidationError
from app.core.security import (
    create_access_token,
    create_credentials_exception,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.repositories.admin import AdminRepository
from app.schemas.auth import AdminCreate, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication and authorization."""

    def __init__(self, db: Session):
        self.db = db
        self.admin_repo = AdminRepository(db)

    def authenticate_admin(self, username: str, password: str) -> Optional[Any]:
        """Authenticate an administrator."""
        admin = self.admin_repo.get_by_username(username)
        if not admin:
            return None

        if not admin.is_active:
            return None

        if not verify_password(password, admin.hashed_password):
            return None

        # Update last login
        self.admin_repo.update_last_login(admin.id)

        return admin

    def create_tokens(self, admin: Any) -> TokenResponse:
        """Create access and refresh tokens for an admin."""
        # Determine admin role and scopes
        role = "superuser" if admin.is_superuser else "admin"
        scopes = ["admin", "admin_portal", "api"] if admin.is_active else []
        
        token_data = {
            "sub": admin.username,
            "admin_id": admin.id,
            "user_id": admin.id,  # Required by get_current_user
            "user_type": "admin",
            "is_superuser": admin.is_superuser
        }

        access_token = create_access_token(
            token_data, 
            scopes=scopes,
            user_role=role
        )
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Create a new access token using a refresh token."""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise create_credentials_exception("Invalid refresh token")

        username = payload.get("sub")
        admin_id = payload.get("admin_id")

        if not username or not admin_id:
            raise create_credentials_exception("Invalid token payload")

        # Verify admin still exists and is active
        admin = self.admin_repo.get(admin_id)
        if not admin or not admin.is_active:
            raise create_credentials_exception("Admin account not found or inactive")

        # Create new tokens
        return self.create_tokens(admin)

    def get_current_admin(self, token: str) -> Any:
        """Get current admin from access token."""
        payload = verify_token(token, "access")
        if not payload:
            raise create_credentials_exception()

        username = payload.get("sub")
        if not username:
            raise create_credentials_exception()

        admin = self.admin_repo.get_by_username(username)
        if not admin or not admin.is_active:
            raise create_credentials_exception()

        return admin

    def change_password(self, admin_id: int, old_password: str, new_password: str) -> bool:
        """Change password for an administrator."""
        # Get the admin
        admin = self.admin_repo.get(admin_id)
        if not admin:
            raise ValidationError("Administrator not found")
        
        # Verify old password
        if not verify_password(old_password, admin.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Hash new password
        new_hashed_password = get_password_hash(new_password)
        
        # Update password
        try:
            self.admin_repo.update(admin_id, {"hashed_password": new_hashed_password})
            logger.info(f"Password changed successfully for admin {admin.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to change password for admin {admin_id}: {e}")
            raise ValidationError("Failed to change password")

    def create_first_admin(self) -> Dict[str, Any]:
        """Create the first administrator account."""
        # Check if any admin already exists
        if self.admin_repo.has_any_admin():
            raise ValidationError("Administrator account already exists")

        # Create default admin
        admin_data = {
            "username": "admin",
            "email": "admin@ispframework.local",
            "full_name": "System Administrator",
            "hashed_password": get_password_hash("admin123"),
            "is_active": True,
            "is_superuser": True,
            "role": "admin",
            "permissions": ["*"],  # All permissions
        }

        try:
            admin = self.admin_repo.create(admin_data)
            logger.info(f"Created first admin user with id {admin.id}")

            return {
                "message": "First admin user created successfully",
                "username": "admin",
                "password": "admin123",
                "warning": "Please change the default password immediately!",
            }
        except Exception as e:
            logger.error(f"Error creating first admin: {e}")
            raise

    def create_admin(self, admin_data: AdminCreate, created_by_admin: Any) -> Any:
        """Create a new administrator account."""
        # Check if username exists
        if self.admin_repo.username_exists(admin_data.username):
            raise DuplicateError(f"Username '{admin_data.username}' already exists")

        # Check if email exists
        if self.admin_repo.email_exists(admin_data.email):
            raise DuplicateError(f"Email '{admin_data.email}' already exists")

        # Hash password
        hashed_password = get_password_hash(admin_data.password)

        # Create admin data dict
        admin_dict = admin_data.model_dump(exclude={"password"})
        admin_dict["hashed_password"] = hashed_password
        admin_dict["is_active"] = True

        try:
            admin = self.admin_repo.create(admin_dict)
            logger.info(
                f"Admin {created_by_admin.username} created new admin {admin.id}"
            )
            return admin
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            raise

    def change_password(
        self, admin_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change administrator password."""
        admin = self.admin_repo.get_or_404(admin_id)

        # Verify old password
        if not verify_password(old_password, admin.hashed_password):
            raise ValidationError("Current password is incorrect")

        # Hash new password
        new_hashed_password = get_password_hash(new_password)

        try:
            self.admin_repo.update(
                admin_id,
                {
                    "hashed_password": new_hashed_password,
                    "password_changed_at": "NOW()",
                },
            )
            logger.info(f"Admin {admin_id} changed password")
            return True
        except Exception as e:
            logger.error(f"Error changing password for admin {admin_id}: {e}")
            raise

    def deactivate_admin(self, admin_id: int, deactivated_by: Any) -> Any:
        """Deactivate an administrator."""
        if admin_id == deactivated_by.id:
            raise ValidationError("Cannot deactivate your own account")

        try:
            admin = self.admin_repo.deactivate_admin(admin_id)
            logger.info(f"Admin {deactivated_by.username} deactivated admin {admin_id}")
            return admin
        except Exception as e:
            logger.error(f"Error deactivating admin {admin_id}: {e}")
            raise
