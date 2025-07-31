import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auth import Administrator
from app.services.auth import AuthService
from app.services.oauth import OAuthService

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Administrator:
    """
    Dependency to get the current authenticated administrator.
    Validates both OAuth and JWT tokens and returns the administrator object.
    """
    try:
        # Extract token from credentials
        token = credentials.credentials

        # Initialize services
        auth_service = AuthService(db)
        oauth_service = OAuthService(db)

        # First try OAuth token validation
        try:
            oauth_token = oauth_service.validate_access_token(token)
            if oauth_token and oauth_token.user_id:
                admin = auth_service.admin_repo.get(oauth_token.user_id)
                if admin and admin.is_active:
                    logger.info(f"Authenticated via OAuth token: {admin.username}")
                    return admin
        except Exception as oauth_error:
            logger.debug(f"OAuth token validation failed: {oauth_error}")

        # Fallback to JWT token validation
        try:
            admin = auth_service.get_current_admin(token)
            if admin:
                logger.info(f"Authenticated via JWT token: {admin.username}")
                return admin
        except Exception as jwt_error:
            logger.debug(f"JWT token validation failed: {jwt_error}")

        # If both methods fail, raise authentication error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_admin(
    current_admin: Administrator = Depends(get_current_admin),
) -> Administrator:
    """
    Dependency to get the current authenticated and active administrator.
    """
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive administrator account",
        )

    return current_admin


# Optional: Admin role checking dependencies
async def require_super_admin(
    current_admin: Administrator = Depends(get_current_admin),
) -> Administrator:
    """
    Dependency that requires super admin privileges.
    """
    if current_admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required",
        )

    return current_admin


async def require_admin_or_manager(
    current_admin: Administrator = Depends(get_current_admin),
) -> Administrator:
    """
    Dependency that requires admin or manager privileges.
    """
    allowed_roles = ["super_admin", "admin", "manager"]
    if current_admin.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or manager privileges required",
        )

    return current_admin
