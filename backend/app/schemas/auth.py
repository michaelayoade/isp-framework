from pydantic import EmailStr, Field
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")


class TokenData(BaseModel):
    """Schema for token payload data."""
    username: Optional[str] = None
    admin_id: Optional[int] = None


class AdminBase(BaseModel):
    """Base administrator schema."""
    username: str = Field(..., min_length=3, max_length=100, description="Administrator username")
    email: EmailStr = Field(..., description="Administrator email")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: str = Field("admin", max_length=50, description="Administrator role")
    permissions: List[str] = Field(default_factory=list, description="List of permissions")


class AdminCreate(AdminBase):
    """Schema for creating a new administrator."""
    password: str = Field(..., min_length=8, description="Administrator password")
    is_superuser: bool = Field(False, description="Is superuser")


class AdminUpdate(BaseModel):
    """Schema for updating an administrator."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class Admin(AdminBase):
    """Schema for administrator response."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    



class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    def passwords_match(self) -> bool:
        """Check if new passwords match."""
        return self.new_password == self.confirm_password
