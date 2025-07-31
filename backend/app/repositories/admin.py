import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.auth import Administrator
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AdminRepository(BaseRepository[Administrator]):
    """Repository for administrator-specific database operations."""

    def __init__(self, db: Session):
        super().__init__(Administrator, db)

    def get_by_username(self, username: str) -> Optional[Administrator]:
        """Get administrator by username."""
        return self.get_by_field("username", username)

    def get_by_email(self, email: str) -> Optional[Administrator]:
        """Get administrator by email."""
        return self.get_by_field("email", email)

    def get_active_admins(self) -> List[Administrator]:
        """Get all active administrators."""
        return self.get_all(filters={"is_active": True})

    def get_superusers(self) -> List[Administrator]:
        """Get all superuser administrators."""
        return self.get_all(filters={"is_superuser": True})

    def update_last_login(self, admin_id: int) -> Administrator:
        """Update administrator's last login timestamp."""
        return self.update(admin_id, {"last_login": datetime.utcnow()})

    def deactivate_admin(self, admin_id: int) -> Administrator:
        """Deactivate an administrator."""
        return self.update(admin_id, {"is_active": False})

    def activate_admin(self, admin_id: int) -> Administrator:
        """Activate an administrator."""
        return self.update(admin_id, {"is_active": True})

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username already exists."""
        query = self.db.query(Administrator).filter(Administrator.username == username)
        if exclude_id:
            query = query.filter(Administrator.id != exclude_id)
        return query.first() is not None

    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email already exists."""
        query = self.db.query(Administrator).filter(Administrator.email == email)
        if exclude_id:
            query = query.filter(Administrator.id != exclude_id)
        return query.first() is not None

    def has_any_admin(self) -> bool:
        """Check if any administrator exists in the system."""
        return self.db.query(Administrator).first() is not None
