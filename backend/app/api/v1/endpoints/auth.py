import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.models import Administrator
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate and get access token (form data)."""
    auth_service = AuthService(db)

    # Authenticate admin
    admin = auth_service.authenticate_admin(form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    tokens = auth_service.create_tokens(admin)
    logger.info(f"Admin {admin.username} logged in successfully")

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login_json(
    login_data: LoginRequest, db: Session = Depends(get_db)
):
    """Authenticate and get access token (JSON data)."""
    auth_service = AuthService(db)

    # Authenticate admin
    admin = auth_service.authenticate_admin(login_data.username, login_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    tokens = auth_service.create_tokens(admin)
    logger.info(f"Admin {admin.username} logged in successfully via JSON")

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)

    try:
        tokens = auth_service.refresh_access_token(refresh_data.refresh_token)
        return tokens
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me")
async def get_current_user_info(
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get current authenticated admin information."""
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "email": current_admin.email,
        "full_name": current_admin.full_name,
        "role": current_admin.role,
        "is_active": current_admin.is_active,
        "is_superuser": current_admin.is_superuser,
        "last_login": current_admin.last_login,
    }


@router.post("/setup")
async def setup_admin(admin_data: dict, db: Session = Depends(get_db)):
    """Setup endpoint for initial admin creation."""
    auth_service = AuthService(db)

    try:
        # Check if any admin already exists
        existing_admins = auth_service.admin_repo.count()
        if existing_admins > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin already exists. Setup is only available for initial configuration.",
            )

        # Create the admin
        admin = auth_service.admin_repo.create(
            {
                "username": admin_data.get("username"),
                "email": admin_data.get("email"),
                "hashed_password": auth_service.admin_repo.hash_password(
                    admin_data.get("password")
                ),
                "full_name": admin_data.get("full_name", admin_data.get("username")),
                "is_active": True,
                "is_superuser": True,
            }
        )

        logger.info(f"Initial admin created: {admin.username}")
        return {
            "message": "Admin created successfully",
            "admin_id": admin.id,
            "username": admin.username,
            "email": admin.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup admin creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin",
        )


@router.post("/setup/create-admin")
async def create_first_admin(db: Session = Depends(get_db)):
    """Create the first administrator account (legacy setup endpoint)."""
    auth_service = AuthService(db)

    try:
        result = auth_service.create_first_admin()
        return result
    except Exception as e:
        logger.error(f"Setup admin creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
