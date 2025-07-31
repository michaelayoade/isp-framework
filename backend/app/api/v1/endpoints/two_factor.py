from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.two_factor import TwoFactorService, ApiKeyService
from app.api.dependencies import get_current_admin
from app.models import Administrator
from app.schemas.two_factor import (
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorStatusResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyListResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Set up TOTP 2FA for the current administrator
    Returns QR code and manual entry key
    """
    try:
        tfa_service = TwoFactorService(db)
        setup_data = tfa_service.setup_totp(current_admin.id)
        
        return TwoFactorSetupResponse(
            secret_key=setup_data["secret_key"],
            qr_code=setup_data["qr_code"],
            manual_entry_key=setup_data["manual_entry_key"],
            issuer=setup_data["issuer"],
            account_name=setup_data["account_name"]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up 2FA"
        )


@router.post("/verify-setup")
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA setup and enable 2FA
    Returns backup codes
    """
    try:
        tfa_service = TwoFactorService(db)
        result = tfa_service.verify_totp_setup(current_admin.id, request.code)
        
        return {
            "enabled": result["enabled"],
            "backup_codes": result["backup_codes"],
            "message": result["message"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify 2FA setup"
        )


@router.post("/verify")
async def verify_2fa_code(
    request: TwoFactorVerifyRequest,
    req: Request,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA code for authentication
    """
    try:
        tfa_service = TwoFactorService(db)
        client_ip = req.client.host
        
        is_valid = tfa_service.verify_totp_code(
            current_admin.id, 
            request.code, 
            client_ip
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        return {"verified": True, "message": "2FA code verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA code verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify 2FA code"
        )


@router.post("/disable")
async def disable_2fa(
    request: TwoFactorVerifyRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA for the current administrator
    Requires current 2FA code for verification
    """
    try:
        tfa_service = TwoFactorService(db)
        success = tfa_service.disable_2fa(current_admin.id, request.code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code or 2FA not enabled"
            )
        
        return {"disabled": True, "message": "2FA has been disabled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/status", response_model=TwoFactorStatusResponse)
async def get_2fa_status(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get 2FA status for the current administrator
    """
    try:
        tfa_service = TwoFactorService(db)
        status_data = tfa_service.get_2fa_status(current_admin.id)
        
        return TwoFactorStatusResponse(**status_data)
    
    except Exception as e:
        logger.error(f"2FA status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get 2FA status"
        )


# API Key Management Endpoints
@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the current administrator
    """
    try:
        api_key_service = ApiKeyService(db)
        api_key_data = api_key_service.create_api_key(
            admin_id=current_admin.id,
            key_name=request.key_name,
            scopes=",".join(request.scopes) if request.scopes else "api",
            permissions=request.permissions,
            expires_in_days=request.expires_in_days
        )
        
        return ApiKeyResponse(**api_key_data)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List API keys for the current administrator
    """
    try:
        api_key_service = ApiKeyService(db)
        api_keys = api_key_service.list_api_keys(current_admin.id)
        
        return ApiKeyListResponse(api_keys=api_keys)
    
    except Exception as e:
        logger.error(f"API key listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key
    """
    try:
        api_key_service = ApiKeyService(db)
        success = api_key_service.revoke_api_key(key_id, current_admin.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or access denied"
            )
        
        return {"revoked": True, "message": "API key has been revoked successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================

from fastapi.responses import RedirectResponse

# Redirect old /auth/2fa/* paths to new /auth/two-factor/* paths
@router.get("/{path:path}")
async def redirect_old_2fa_get(path: str):
    """Temporary redirect for old /auth/2fa/* paths"""
    new_path = f"/api/v1/auth/two-factor/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.post("/{path:path}")
async def redirect_old_2fa_post(path: str):
    """Temporary redirect for old /auth/2fa/* paths"""
    new_path = f"/api/v1/auth/two-factor/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.delete("/{path:path}")
async def redirect_old_2fa_delete(path: str):
    """Temporary redirect for old /auth/2fa/* paths"""
    new_path = f"/api/v1/auth/two-factor/{path}"
    return RedirectResponse(url=new_path, status_code=307)
