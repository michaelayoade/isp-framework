"""
Reseller Authentication API Endpoints

Authentication endpoints for reseller login and management in single-tenant ISP Framework.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.reseller_auth import ResellerAuthService
from app.api.v1.dependencies import get_current_admin
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
security = HTTPBearer()


# Pydantic schemas for reseller authentication
class ResellerLoginRequest(BaseModel):
    """Schema for reseller login request"""
    email: EmailStr
    password: str


class ResellerLoginResponse(BaseModel):
    """Schema for reseller login response"""
    access_token: str
    token_type: str
    expires_in: int
    reseller: Dict[str, Any]


class ResellerPasswordSetRequest(BaseModel):
    """Schema for admin setting reseller password"""
    reseller_id: int
    password: str


class ResellerPasswordChangeRequest(BaseModel):
    """Schema for reseller changing their own password"""
    current_password: str
    new_password: str


class ResellerTokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str
    token_type: str
    expires_in: int


@router.post("/login", response_model=ResellerLoginResponse)
async def reseller_login(
    login_data: ResellerLoginRequest,
    db: Session = Depends(get_db)
):
    """Login reseller and return JWT token"""
    try:
        auth_service = ResellerAuthService(db)
        result = auth_service.login_reseller(login_data.email, login_data.password)
        return ResellerLoginResponse(**result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=ResellerTokenRefreshResponse)
async def refresh_reseller_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh reseller access token"""
    try:
        auth_service = ResellerAuthService(db)
        result = auth_service.refresh_token(credentials.credentials)
        return ResellerTokenRefreshResponse(**result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service error"
        )


@router.post("/set-password", status_code=200)
async def set_reseller_password(
    password_data: ResellerPasswordSetRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Set password for reseller (admin only)"""
    try:
        auth_service = ResellerAuthService(db)
        success = auth_service.set_reseller_password(
            password_data.reseller_id, 
            password_data.password
        )
        return {
            "success": success,
            "message": f"Password set successfully for reseller {password_data.reseller_id}"
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password service error"
        )


@router.post("/change-password", status_code=200)
async def change_reseller_password(
    password_data: ResellerPasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Change reseller password (reseller only)"""
    try:
        auth_service = ResellerAuthService(db)
        
        # Get current reseller from token
        current_reseller = auth_service.get_current_reseller(credentials.credentials)
        if not current_reseller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        success = auth_service.change_reseller_password(
            current_reseller.id,
            password_data.current_password,
            password_data.new_password
        )
        
        return {
            "success": success,
            "message": "Password changed successfully"
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change service error"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_reseller_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current reseller information from token"""
    try:
        auth_service = ResellerAuthService(db)
        
        # Get current reseller from token
        current_reseller = auth_service.get_current_reseller(credentials.credentials)
        if not current_reseller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get reseller permissions
        permissions = auth_service.get_reseller_permissions(current_reseller.id)
        
        return {
            "reseller": {
                "id": current_reseller.id,
                "name": current_reseller.name,
                "email": current_reseller.email,
                "code": current_reseller.code,
                "contact_person": current_reseller.contact_person,
                "territory": current_reseller.territory,
                "commission_percentage": float(current_reseller.commission_percentage),
                "customer_limit": current_reseller.customer_limit,
                "is_active": current_reseller.is_active,
                "last_login": current_reseller.last_login,
                "created_at": current_reseller.created_at
            },
            "permissions": permissions
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reseller info service error"
        )


@router.get("/permissions", response_model=Dict[str, Any])
async def get_reseller_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current reseller permissions and access levels"""
    try:
        auth_service = ResellerAuthService(db)
        
        # Get current reseller from token
        current_reseller = auth_service.get_current_reseller(credentials.credentials)
        if not current_reseller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        permissions = auth_service.get_reseller_permissions(current_reseller.id)
        return permissions
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permissions service error"
        )


@router.post("/logout", status_code=200)
async def reseller_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout reseller (invalidate token on client side)"""
    # Note: JWT tokens are stateless, so we can't invalidate them server-side
    # without maintaining a blacklist. For now, we just return success
    # and rely on client-side token removal.
    
    try:
        auth_service = ResellerAuthService(db)
        
        # Verify token is valid
        current_reseller = auth_service.get_current_reseller(credentials.credentials)
        if not current_reseller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "success": True,
            "message": "Logged out successfully. Please remove token from client."
        }
    except Exception:
        # Even if there's an error, we can still return success for logout
        return {
            "success": True,
            "message": "Logged out successfully. Please remove token from client."
        }
