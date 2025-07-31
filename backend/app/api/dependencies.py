from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth import AuthService
from app.models import Administrator
from app.core.security import get_current_user

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service."""
    return AuthService(db)


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Administrator:
    """Get current authenticated administrator."""
    return auth_service.get_current_admin(token)


def get_current_active_admin(
    current_admin: Administrator = Depends(get_current_admin)
) -> Administrator:
    """Get current active administrator."""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin account"
        )
    return current_admin


def get_current_superuser(
    current_admin: Administrator = Depends(get_current_active_admin)
) -> Administrator:
    """Get current superuser administrator."""
    if not current_admin.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_admin


def get_current_admin_user(
    current_user: dict = Security(get_current_user, scopes=["admin"])
) -> dict:
    """Get current admin user with admin scope validation."""
    return current_user


def validate_pagination(
    page: int = 1,
    per_page: int = 25
) -> tuple[int, int]:
    """Validate and normalize pagination parameters."""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 25
    if per_page > 100:
        per_page = 100
    
    return page, per_page
