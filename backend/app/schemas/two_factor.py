from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TwoFactorSetupResponse(BaseModel):
    """Response for 2FA setup"""

    secret_key: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code as base64 data URL")
    manual_entry_key: str = Field(
        ..., description="Manual entry key for authenticator apps"
    )
    issuer: str = Field(..., description="Issuer name")
    account_name: str = Field(..., description="Account name (email)")


class TwoFactorVerifyRequest(BaseModel):
    """Request for 2FA code verification"""

    code: str = Field(..., description="6-digit TOTP code", min_length=6, max_length=6)


class TwoFactorStatusResponse(BaseModel):
    """Response for 2FA status"""

    enabled: bool = Field(..., description="Whether 2FA is enabled")
    method: Optional[str] = Field(None, description="2FA method (totp, sms, email)")
    verified_at: Optional[datetime] = Field(
        None, description="When 2FA was first verified"
    )
    last_used: Optional[datetime] = Field(
        None, description="Last successful 2FA verification"
    )
    backup_codes_remaining: int = Field(
        ..., description="Number of unused backup codes"
    )
    locked_until: Optional[datetime] = Field(None, description="When 2FA lock expires")


class ApiKeyCreateRequest(BaseModel):
    """Request to create an API key"""

    key_name: str = Field(..., description="Name for the API key")
    scopes: Optional[List[str]] = Field(["api"], description="API key scopes")
    permissions: Optional[Dict[str, Any]] = Field(
        None, description="Additional permissions"
    )
    expires_in_days: Optional[int] = Field(
        None, description="Expiration in days (optional)"
    )


class ApiKeyResponse(BaseModel):
    """Response for API key creation"""

    api_key: str = Field(..., description="The API key (only shown once)")
    key_id: int = Field(..., description="API key ID")
    key_name: str = Field(..., description="API key name")
    key_prefix: str = Field(..., description="API key prefix for identification")
    scopes: List[str] = Field(..., description="API key scopes")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    created_at: datetime = Field(..., description="Creation timestamp")


class ApiKeyInfo(BaseModel):
    """API key information (without the actual key)"""

    id: int = Field(..., description="API key ID")
    key_name: str = Field(..., description="API key name")
    key_prefix: str = Field(..., description="API key prefix")
    scopes: List[str] = Field(..., description="API key scopes")
    is_active: bool = Field(..., description="Whether the key is active")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(..., description="Total usage count")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    created_at: datetime = Field(..., description="Creation timestamp")


class ApiKeyListResponse(BaseModel):
    """Response for listing API keys"""

    api_keys: List[ApiKeyInfo] = Field(..., description="List of API keys")


class TwoFactorSessionRequest(BaseModel):
    """Request to create 2FA session"""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TwoFactorSessionResponse(BaseModel):
    """Response for 2FA session creation"""

    session_token: str = Field(..., description="Temporary session token")
    expires_in: int = Field(..., description="Session expiration in seconds")
    message: str = Field(..., description="Instructions for user")


class TwoFactorSessionVerifyRequest(BaseModel):
    """Request to verify 2FA session"""

    session_token: str = Field(..., description="2FA session token")
    code: str = Field(..., description="6-digit TOTP code", min_length=6, max_length=6)


class BackupCodesResponse(BaseModel):
    """Response for backup codes generation"""

    backup_codes: List[str] = Field(..., description="List of backup codes")
    message: str = Field(..., description="Instructions for backup codes")


class TwoFactorDisableRequest(BaseModel):
    """Request to disable 2FA"""

    current_password: str = Field(..., description="Current password for verification")
    verification_code: str = Field(
        ..., description="Current 2FA code", min_length=6, max_length=6
    )
